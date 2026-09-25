#!/usr/bin/env node
/**
 * Claude 가 쓰는 에디터 조작 CLI.
 *
 *   node cli.mjs start <문서.hwpx>     서버를 띄우고 에디터 앱 창(없으면 브라우저)에 연다 [--browser]
 *   node cli.mjs run <ops.json | ->    JSON 명령 배열을 에디터에 적용 (한 트랜잭션, undo 1스텝)
 *   node cli.mjs text                  현재 본문 텍스트
 *   node cli.mjs outline [시작 끝]      좌표(p12, T1r2c1)가 붙은 문서 개요
 *   node cli.mjs state                 문서 상태와 사용자 커서(셀 좌표, 선택한 글자)
 *   node cli.mjs goto <좌표>            사용자 화면의 커서를 그 문단이나 셀로 옮긴다
 *   node cli.mjs inspect | slots       행정문서 표기 검수 / 아직 안 채운 칸
 *   node cli.mjs tools                 편집 도구 25종 정의(이름, 설명, 인자)
 *   node cli.mjs changes [--all]       아직 안 읽은 사용자 수정 내역 (읽으면 읽음 처리)
 *   node cli.mjs save [출력.hwpx]      새 판으로 저장 (기본: <이름>_<YYMMDD>_<NN>.hwpx, 덮어쓰기 없음)
 *   node cli.mjs undo                  마지막 배치 되돌리기
 *   node cli.mjs log [N | --all]       작업 기록(시작, 불러옴, 편집, 화면 저장 포함 저장, 종료, 오류). 비우지 않고 쌓인다
 *   node cli.mjs list                  떠 있는 에디터 전부(세션마다 하나. * 는 이 세션의 것)
 *   node cli.mjs status | stop
 */
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import net from 'node:net';
import { spawn, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { readZip, fixHfFields } from './hwpx-zip.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));

/**
 * 에디터는 세션마다 하나다(2026-09-25 — 공용 하나였을 때 두 세션이 서로의 문서를 덮어썼다).
 * 인스턴스 이름: HWPX_EDITOR_INSTANCE → Claude Code 세션 ID 앞 8자 → default.
 * 상태 폴더는 ROOT/<이름>/, 포트는 7780 부터 빈 것을 골라 그 폴더의 port 파일에 적는다.
 * 옛 공용 에디터(ROOT 바로 아래 상태, 포트 7780)가 떠 있고 이 세션의 에디터가 없으면 그것을 계속 쓴다(작업 중인 세션을 끊지 않는다).
 */
const ROOT = path.join(os.homedir(), '.claude', 'cache', 'hwpx-editor');
const INSTANCE = process.env.HWPX_EDITOR_INSTANCE || (process.env.CLAUDE_CODE_SESSION_ID || '').slice(0, 8) || 'default';
const probe = async (port) => { try { return await (await fetch(`http://127.0.0.1:${port}/api/health`, { signal: AbortSignal.timeout(1500) })).json(); } catch { return null; } };
const readPort = (dir) => { try { return Number(fs.readFileSync(path.join(dir, 'port'), 'utf8')) || null; } catch { return null; } };
let STATE_DIR = process.env.HWPX_EDITOR_STATE || path.join(ROOT, INSTANCE);
let PORT = Number(process.env.HWPX_EDITOR_PORT) || readPort(STATE_DIR);
if (!PORT && !process.env.HWPX_EDITOR_STATE && process.argv[2] !== 'start' && process.argv[2] !== 'list') {
  const legacy = await probe(7780);
  if (legacy && path.resolve(legacy.stateDir || '') === path.resolve(ROOT)) { STATE_DIR = ROOT; PORT = 7780; }
}
PORT ||= 7780;
let BASE = `http://127.0.0.1:${PORT}`;
fs.mkdirSync(STATE_DIR, { recursive: true });

/** start 가 쓸 포트: 이 인스턴스 서버가 살아 있으면 그 포트, 아니면 7780 부터 비어 있는 포트. */
async function allocatePort() {
  const mine = readPort(STATE_DIR);
  if (mine && (await probe(mine))) return mine;
  for (let p = 7780; p < 7880; p++) {
    if (await probe(p)) continue;
    const free = await new Promise((res) => {
      const s = net.createServer().once('error', () => res(false)).once('listening', () => s.close(() => res(true)));
      s.listen(p, '127.0.0.1');
    });
    if (free) return p;
  }
  throw new Error('빈 포트가 없다(7780~7879)');
}
const SESSION = path.join(STATE_DIR, 'session.json');
const CHANGES = path.join(STATE_DIR, 'changes.jsonl');
const SEEN = path.join(STATE_DIR, 'changes.seen');
const OPS = path.join(STATE_DIR, 'ops.jsonl');
const OPS_SEEN = path.join(STATE_DIR, 'ops.seen');
const APP_PID = path.join(STATE_DIR, 'app.pid');

const out = (obj) => process.stdout.write((typeof obj === 'string' ? obj : JSON.stringify(obj, null, 2)) + '\n');
const die = (msg) => { process.stderr.write(msg + '\n'); process.exit(1); };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function health() {
  try { return await (await fetch(`${BASE}/api/health`)).json(); } catch { return null; }
}

/** 작업 기록(editor-log.jsonl)에 한 줄. 서버가 없으면 조용히 넘어간다. */
async function postLog(ev, data = {}) {
  try { await fetch(`${BASE}/api/log`, { method: 'POST', body: JSON.stringify({ ev, ...data }) }); } catch { /* 서버 꺼짐 */ }
}

const LOG = path.join(STATE_DIR, 'editor-log.jsonl');
const kb = (n) => (n == null ? '' : n < 1024 ? `${n}B` : `${(n / 1024).toFixed(1)}KB`);
const LAYOUT = { hancom: '한글 줄 배치 적용', 'hancom-cache': '한글 줄 배치(캐시)', rhwp: 'rhwp 표 높이 보정(한글 없음)', strip: '더미 줄 배치만 걷음 — 표가 겹칠 수 있다', stored: '저장된 줄 배치 그대로', raw: 'hwp 그대로' };
function formatLog(e) {
  const t = new Date(e.ts).toLocaleString('sv-SE').slice(5, 16);
  const who = e.by === 'user' ? '사용자' : e.by === 'claude' ? 'Claude' : '';
  switch (e.ev) {
    case 'start': return `${t}  시작      ${e.file}`;
    case 'load': return `${t}  불러옴    ${e.doc} — ${LAYOUT[e.layout] ?? e.layout}${e.tables ? ` ${e.tables}개` : ''}${e.note ? ` (${e.note})` : ''}${e.error ? ` (${e.error})` : ''}`;
    case 'open': return `${t}  열림      ${e.doc} ${kb(e.bytes)}`;
    case 'edit': return `${t}  ${who} 편집 ${e.formatOnly ? '서식이나 개체만' : `${e.count}곳 ${e.refs.join(' ')}${e.count > e.refs.length ? ' …' : ''}`}${e.at ? ` (커서 ${e.at})` : ''}`;
    case 'save': return `${t}  ${who} 저장 ${e.path ?? e.name} ${kb(e.bytes)}${e.via ? ` (${e.via})` : ''}`;
    case 'open-file': return `${t}  ${who} 다른 파일 열기 ${e.names.join(', ')} (${e.via})`;
    case 'error': return `${t}  오류      ${e.cmd ?? ''} ${e.error}`;
    case 'stop': return `${t}  종료`;
    default: return `${t}  ${e.ev} ${JSON.stringify(e)}`;
  }
}

async function cmd(body) {
  const res = await fetch(`${BASE}/api/cmd`, { method: 'POST', body: JSON.stringify(body) });
  const r = await res.json();
  if (!r.ok) die(`실패: ${r.error}`);
  return r;
}

async function ensureServer() {
  if (await health()) return;
  if (!fs.existsSync(path.join(HERE, 'studio-dist', 'index.html'))) die('studio-dist 가 없다. 먼저 node setup.mjs 로 빌드한다.');
  const child = spawn(process.execPath, [path.join(HERE, 'server.mjs')], {
    detached: true, stdio: 'ignore', windowsHide: true,
    env: { ...process.env, HWPX_EDITOR_PORT: String(PORT), HWPX_EDITOR_STATE: STATE_DIR },
  });
  child.unref();
  fs.writeFileSync(path.join(STATE_DIR, 'port'), String(PORT));
  for (let i = 0; i < 50; i++) { if (await health()) return; await sleep(200); }
  die('서버가 뜨지 않았다');
}

/**
 * 에디터 앱 창(app.py, WebView2)을 연다. 한/글 단축키 Ctrl+N 계열이 되는 유일한 방법이다.
 * 파이썬이나 pywebview 가 없으면 false 를 돌려주고, 호출자가 브라우저로 연다.
 */
function openAppWindow(url, docName) {
  const py = process.platform === 'win32' ? 'python' : 'python3';
  const check = spawnSync(py, ['-c', 'import webview'], { stdio: 'ignore', windowsHide: true });
  if (check.status !== 0) return false;
  // 창이 여럿일 수 있으니 제목에 문서 이름과 인스턴스를 넣어 가른다
  const title = `HWPX 에디터 · ${docName} · ${path.basename(STATE_DIR)}`;
  const child = spawn(py, [path.join(HERE, 'app.py'), url, title], { detached: true, stdio: 'ignore', env: { ...process.env, HWPX_EDITOR_STATE: STATE_DIR } });
  fs.writeFileSync(APP_PID, String(child.pid));
  child.unref();
  return true;
}

/**
 * 앞서 띄운 앱 창이 살아 있으면 그 pid. 서버만 내렸다 다시 띄우면 옛 창이 새 서버에 다시 붙으므로,
 * 이것을 보지 않고 창을 또 열면 두 창이 명령을 나눠 받아 측정값이 뒤섞였다(2026-09-25 실측).
 */
function aliveAppPid() {
  try {
    const pid = Number(fs.readFileSync(APP_PID, 'utf8'));
    process.kill(pid, 0);
    return pid;
  } catch { return null; }
}

function openBrowser(url) {
  if (process.platform === 'win32') spawn('cmd', ['/c', 'start', '', url], { detached: true, stdio: 'ignore' }).unref();
  else spawn(process.platform === 'darwin' ? 'open' : 'xdg-open', [url], { detached: true, stdio: 'ignore' }).unref();
}

/** KS X 6101 §15(암호화), §16(전자서명). 편집하면 안 되는 hwpx 인지 본다. */
function editBlocker(file) {
  if (!/\.hwpx$/i.test(file)) return null;
  const z = readZip(fs.readFileSync(file));
  if (!z) return 'zip 으로 읽히지 않는다(손상된 hwpx)';
  const entry = (name) => z.find((e) => e.name === name);
  if (entry('META-INF/signatures.xml')) return '전자서명 문서다. 편집하면 서명이 무효가 된다(KS X 6101 §16)';
  if (entry('META-INF/manifest.xml')?.data.toString('utf8').includes('encryption-data')) return '암호화 문서다. 편집할 수 없다(KS X 6101 §15)';
  return null;
}

/**
 * 저장할 때마다 새 판을 만든다: <이름>_<YYMMDD>_<NN>.hwpx (스킬 build_version.py 와 같은 규칙).
 * 원본 이름 끝의 _YYMMDD 또는 _YYMMDD_NN 은 떼고 오늘 날짜의 최대 순번 + 1 을 붙인다.
 */
function nextVersion(source) {
  const dir = path.dirname(source);
  const prefix = path.basename(source).replace(/\.hwpx?$/i, '').replace(/_\d{6}(_\d{2})?$/, '');
  const d = new Date();
  const today = `${String(d.getFullYear()).slice(2)}${String(d.getMonth() + 1).padStart(2, '0')}${String(d.getDate()).padStart(2, '0')}`;
  const esc = prefix.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const pat = new RegExp(`^${esc}_${today}_(\\d{2})\\.hwpx$`);
  const max = Math.max(0, ...fs.readdirSync(dir).map((f) => Number(pat.exec(f)?.[1] ?? 0)));
  return path.join(dir, `${prefix}_${today}_${String(max + 1).padStart(2, '0')}.hwpx`);
}

function readOps() {
  try { return fs.readFileSync(OPS, 'utf8').split('\n').filter(Boolean).map((l) => JSON.parse(l)); } catch { return []; }
}

const localTime = (t) => new Date(t).toTimeString().slice(0, 8);

// 서식 속성 이름과 값(글자 크기는 1/100 pt)
const PROP = {
  fontSize: ['글자 크기', (v) => `${v / 100}pt`], lineSpacing: ['줄 간격', (v) => `${v}%`], lineSpacingType: ['줄 간격 종류'],
  bold: ['진하게'], italic: ['기울임'], underline: ['밑줄'], strikethrough: ['취소선'], textColor: ['글자 색'],
  shadeColor: ['음영 색'], fontId: ['글꼴'], fontIds: ['글꼴'], ratios: ['장평', (v) => `${v?.[0]}%`],
  spacings: ['자간', (v) => `${v?.[0]}%`], relativeSizes: ['상대 크기'], superscript: ['위 첨자'], subscript: ['아래 첨자'],
  alignment: ['정렬'], indent: ['들여쓰기'], marginLeft: ['왼쪽 여백'], marginRight: ['오른쪽 여백'],
  spacingBefore: ['문단 위'], spacingAfter: ['문단 아래'], keepWithNext: ['다음 문단과 함께'], keepLines: ['문단 보호'],
  widowOrphan: ['외톨이줄 보호'], pageBreakBefore: ['앞에서 쪽 나눔'], headType: ['문단 머리'],
};
const propText = (k, [a, b]) => {
  const [name, fmt] = PROP[k] ?? [k];
  const f = (v) => (v === undefined ? '?' : fmt ? fmt(v) : typeof v === 'string' ? v : JSON.stringify(v));
  return `${name} ${f(a)} → ${f(b)}`;
};

/** 이어 친 글자(같은 자리, 붙은 위치)를 한 줄로 묶는다. */
function coalesceOps(ops) {
  const outOps = [];
  for (const o of ops) {
    const last = outOps[outOps.length - 1];
    if (last && o.type === 'insertText' && last.type === 'insertText' && last.act === o.act && last.atKey === o.atKey &&
        last.end === o.off && o.t - last.t < 5000) {
      outOps[outOps.length - 1] = { ...last, text: last.text + o.text, end: o.end, t: o.t };
    } else outOps.push({ ...o });
  }
  return outOps;
}

/** 실시간 편집 기록 한 줄: [시각] 동작 자리 내용. 서식은 속성: 전 → 후 */
function formatOp(o) {
  const act = { undo: '되돌리기 ', redo: '다시 실행 ', reserve: '' }[o.act] ?? '';
  let what = '';
  if (o.type === 'insertText') what = `「${o.text}」`;
  else if (o.type === 'deleteText') what = o.text ? `「${o.text}」` : `${o.count}자`;
  if (o.props && Object.keys(o.props).length) what = Object.entries(o.props).map(([k, v]) => propText(k, v)).join(', ');
  return `[${localTime(o.t)}] ${act}${o.label}${o.at ? `  ${o.at}` : ''}${what ? `  ${what}` : ''}`;
}

function readChanges() {
  try { return fs.readFileSync(CHANGES, 'utf8').split('\n').filter(Boolean).map((l) => JSON.parse(l)); } catch { return []; }
}

/** 커서 설명: 셀 안이면 셀 좌표, 본문이면 문단 좌표, 선택한 글자가 있으면 그 글자. */
function describeCursor(cur) {
  if (!cur) return '';
  const at = cur.cell ? (cur.cell.ref ?? `표 셀(문단 p${cur.cell.para})`) : `p${cur.para}`;
  const sel = cur.selectedText ? `, 선택: 「${cur.selectedText.slice(0, 60)}」` : '';
  return ` (커서: ${at}${sel})`;
}

function formatChange(c) {
  const head = `[${localTime(c.ts)}] ${c.source === 'user' ? '사용자' : c.source === 'claude' ? 'Claude' : '열림'}`;
  const cur = describeCursor(c.cursor);
  if (c.note) return `${head} ${c.note}`;
  if (c.formatOnly) return `${head} 서식이나 개체만 바뀜(글자 변화 없음)${cur}`;
  const lines = c.coords
    ? c.diff.map((d) => `  ${d.op} ${d.ref.padEnd(8)} │ ${d.op === '~' ? `${d.before} → ${d.after}` : (d.after ?? d.before)}`)
    : c.diff.map((d) => `  ${d.op}${String(d.line).padStart(4)} │ ${d.text}`);
  return [`${head}${cur}`, ...lines].join('\n');
}

const [, , sub, ...args] = process.argv;
switch (sub) {
  case 'start': {
    const file = args[0] && path.resolve(args[0]);
    if (!file || !fs.existsSync(file)) die('사용법: start <문서.hwpx|.hwp>');
    const blocker = editBlocker(file);
    if (blocker && !args.includes('--force')) die(`열지 않음: ${blocker}. 사용자가 원하면 --force`);
    fs.mkdirSync(STATE_DIR, { recursive: true });
    fs.writeFileSync(SESSION, JSON.stringify({ source: file, startedAt: new Date().toISOString() }, null, 2));
    fs.writeFileSync(CHANGES, '');
    fs.writeFileSync(SEEN, '0');
    fs.writeFileSync(OPS, '');
    fs.writeFileSync(OPS_SEEN, '0');
    if (!process.env.HWPX_EDITOR_PORT) { PORT = await allocatePort(); BASE = `http://127.0.0.1:${PORT}`; }
    await ensureServer();
    await postLog('start', { file, instance: path.basename(STATE_DIR), port: PORT });
    let h = await health();
    if (!h.browser && aliveAppPid()) {                // 옛 앱 창이 새 서버에 다시 붙기를 기다린다
      for (let i = 0; i < 20 && !h.browser; i++) { await sleep(500); h = await health(); }
    }
    if (h.browser) await cmd({ type: 'open' });       // 이미 열린 탭이 있으면 그 탭에 새 문서를 연다
    else if (!args.includes('--no-browser')) {
      const url = `http://localhost:${PORT}/`;
      // 기본은 앱 창(한/글 단축키 전부). --browser 면 브라우저 탭(Ctrl+N 계열은 Ctrl+M 으로 대신).
      if (args.includes('--browser') || !openAppWindow(url, path.basename(file))) openBrowser(url);
    }
    // 스킬 파이프라인 산출물은 서버가 한글로 줄 배치를 계산해 보내므로(hancom_layout.py) 넉넉히 기다린다.
    for (let i = 0; i < 180; i++) {
      if (readChanges().some((c) => c.source === 'open')) { out(`열림: ${file}\n에디터: http://localhost:${PORT}/`); process.exit(0); }
      await sleep(500);
    }
    die('브라우저에서 문서가 열리지 않았다(90초). 탭을 확인한다.');
    break;
  }
  case 'run': {
    const src = args[0] === '-' || !args[0] ? fs.readFileSync(0, 'utf8') : fs.readFileSync(args[0], 'utf8');
    // KS X 6101 §5.3: 본문은 NFC. 맥, 웹에서 온 NFD(자모 분리) 글자는 검색과 치환을 조용히 깨뜨린다.
    const ops = JSON.parse(src, (k, v) => (typeof v === 'string' ? v.normalize('NFC') : v));
    out((await cmd({ type: 'run', ops: Array.isArray(ops) ? ops : [ops] })).result);
    break;
  }
  case 'text': out((await cmd({ type: 'text' })).text); break;
  case 'state': { const r = await cmd({ type: 'state' }); out({ state: r.state, cursor: r.cursor, pageCount: r.pageCount }); break; }
  case 'outline': {
    const opts = args.length === 2 ? { from: Number(args[0]), to: Number(args[1]) } : {};
    out((await cmd({ type: 'outline', opts })).text);
    break;
  }
  case 'goto': out((await cmd({ type: 'goto', ref: args[0] })).result ? `이동: ${args[0]}` : `못 찾음: ${args[0]}`); break;
  case 'inspect': { const r = await cmd({ type: 'inspect' }); out({ docType: r.docType, result: r.result }); break; }
  case 'slots': out((await cmd({ type: 'slots' })).result); break;
  case 'tools': out((await cmd({ type: 'tools' })).result); break;
  case 'undo': out((await cmd({ type: 'undo' })).result); break;
  case 'changes': {
    // ① 실시간 편집 기록(편집 하나가 한 줄, 서식은 전 → 후) ② 글자 diff(문단, 셀 단위 전 → 후). 서식만 바뀐 스냅샷은 ①이 대신한다
    const ops = readOps();
    const opsSeen = args.includes('--all') ? 0 : Number(fs.existsSync(OPS_SEEN) ? fs.readFileSync(OPS_SEEN, 'utf8') : 0);
    const freshOps = ops.slice(opsSeen).filter((o) => o.src === 'user');
    fs.writeFileSync(OPS_SEEN, String(ops.length));
    const all = readChanges();
    const seen = args.includes('--all') ? 0 : Number(fs.existsSync(SEEN) ? fs.readFileSync(SEEN, 'utf8') : 0);
    const fresh = all.slice(seen).filter((c) => c.source === 'user' && !(c.formatOnly && freshOps.length));
    fs.writeFileSync(SEEN, String(all.length));
    const parts = [];
    if (freshOps.length) parts.push(coalesceOps(freshOps).map(formatOp).join('\n'));
    if (fresh.length) parts.push((freshOps.length ? '── 글자 변화(문단, 셀 전 → 후)\n' : '') + fresh.map(formatChange).join('\n'));
    out(parts.length ? parts.join('\n') : '새 사용자 수정 없음');
    break;
  }
  case 'save': {
    const s = JSON.parse(fs.readFileSync(SESSION, 'utf8'));
    const target = args[0] ? path.resolve(args[0]) : nextVersion(s.source);
    if (fs.existsSync(target)) die(`이미 있는 파일은 덮어쓰지 않는다: ${target}`);
    const r = await cmd({ type: 'save' });
    const fix = fixHfFields(Buffer.from(r.base64, 'base64'), r.hfMarkers ?? []);
    fs.writeFileSync(target, fix.buf);
    if (fix.fixed) out(`머리말/꼬리말 쪽 번호 ${fix.fixed}개 보정`);
    for (const why of fix.skipped) out(`⚠ 쪽 번호 보정 못 함: ${why}`);
    await cmd({ type: 'saved', fileName: path.basename(target) });
    await postLog('save', { by: 'claude', path: target, bytes: fix.buf.length, hfFixed: fix.fixed || undefined });
    out(`저장: ${target}`);
    break;
  }
  case 'log': {                                     // 작업 기록. 기본 최근 30줄, --all 전부, 숫자로 줄 수
    let lines = [];
    try { lines = fs.readFileSync(LOG, 'utf8').split('\n').filter(Boolean).map((l) => JSON.parse(l)); } catch { /* 기록 없음 */ }
    const n = args.includes('--all') ? lines.length : Number(args.find((a) => /^\d+$/.test(a)) ?? 30);
    out(lines.length ? lines.slice(-n).map(formatLog).join('\n') : '기록 없음');
    break;
  }
  case 'status': out((await health()) ?? '서버 꺼짐'); break;
  case 'list': {                                    // 떠 있는 에디터 전부(세션마다 하나). * 는 이 세션의 것
    const dirs = [ROOT, ...fs.readdirSync(ROOT, { withFileTypes: true }).filter((d) => d.isDirectory() && d.name !== 'webview').map((d) => path.join(ROOT, d.name))];
    const rows = [];
    for (const dir of dirs) {
      const port = dir === ROOT ? 7780 : readPort(dir);
      if (!port) continue;
      const h = await probe(port);
      if (!h || path.resolve(h.stateDir || '') !== path.resolve(dir)) continue;
      const doc = h.session?.source ? path.basename(h.session.source) : '(문서 없음)';
      rows.push(`${dir === STATE_DIR ? '*' : ' '} ${path.basename(dir).padEnd(10)} 포트 ${port}  창 ${h.browser ? '열림' : '없음'}  ${doc}`);
    }
    out(rows.length ? rows.join('\n') : '떠 있는 에디터 없음');
    break;
  }
  case 'stop': {
    const h = await health();
    let dirty = false;
    if (h?.browser) {
      try {
        const r = await (await fetch(`${BASE}/api/cmd`, { method: 'POST', body: JSON.stringify({ type: 'state', timeoutMs: 5000 }) })).json();
        dirty = Boolean(r.ok && r.state?.dirty);
      } catch { /* 창이 응답하지 않으면 닫는다 */ }
    }
    const pid = aliveAppPid();
    if (pid && dirty && !args.includes('--force')) die('에디터에 저장하지 않은 편집이 있다. save 로 저장하거나, 버리려면 stop --force');
    if (h) await fetch(`${BASE}/api/cmd`, { method: 'POST', body: JSON.stringify({ type: 'shutdown' }) });
    if (pid) { try { process.kill(pid); } catch { /* 이미 닫힘 */ } }
    try { fs.unlinkSync(APP_PID); } catch { /* 없음 */ }
    if (STATE_DIR !== ROOT) { try { fs.unlinkSync(path.join(STATE_DIR, 'port')); } catch { /* 없음 */ } }
    out(pid ? '서버 종료, 앱 창 닫음' : '서버 종료');
    break;
  }
  default: out(fs.readFileSync(fileURLToPath(import.meta.url), 'utf8').split('\n').slice(2, 17).join('\n'));
}
