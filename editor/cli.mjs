#!/usr/bin/env node
/**
 * Claude 가 쓰는 에디터 조작 CLI.
 *
 *   node cli.mjs start [문서.hwpx]     (문서를 빼면 빈 문서 「새 문서.hwpx」를 작업 폴더에 만들어) 서버를 띄우고 앱 창(터미널) 또는 데스크탑 앱 미리보기(.claude/launch.json)에 연다 [--app|--preview|--browser]
 *                                       같은 문서(같은 이름의 다른 판 포함)가 이미 떠 있으면 열지 않는다 — 고칠 것은 run 으로. 꼭 다시 열 때만 --reopen
 *                                       (다른 판이면 --reopen="사용자 요청" 처럼 사유를 적어야 연다)
 *   node cli.mjs hold <상태 폴더>      미리보기가 실행한다 — 떠 있는 에디터 서버에 붙어 있다
 *   node cli.mjs run <ops.json | ->    JSON 명령 배열을 에디터에 적용 (한 트랜잭션, undo 1스텝)
 *   node cli.mjs text                  현재 본문 텍스트
 *   node cli.mjs outline [시작 끝]      좌표(p12, T1r2c1)가 붙은 문서 개요
 *   node cli.mjs state                 문서 상태와 사용자 커서(셀 좌표, 선택한 글자)
 *   node cli.mjs image <그림> [좌표] [--end] [--replace] [--width mm] [--desc 설명] [--wrap square|topbottom|behind|front [--align left|center|right] [--x mm] [--y mm] [--page]]
 *                                       그림을 좌표(p7, T2r0c0) 앞(--end 면 끝)이나 사용자 커서에 넣는다. undo 1스텝
 *   node cli.mjs start 원고.md [--theme ink|--accent #색] [--template report] [--rebuild]
 *                                       마크다운을 빌더(md2hwpx, 디자인 옵션이면 md2hwpx_design)로 같은 이름 .hwpx 로 만들어 연다
 *   node cli.mjs builder <스크립트> <인자… {in} … {out} …>   열린 문서를 빌더 스크립트(scripts/*.py)로 처리해 새 판으로 다시 연다
 *                                       (차트, 도장, 메모 만들기, 합치기 등). Ctrl+Z 기록은 끊기니 되돌리려면 builder --undo
 *   node cli.mjs goto <좌표>            사용자 화면의 커서를 그 문단이나 셀로 옮긴다
 *   node cli.mjs memos [번호] [--json]  문서에 달린 메모(작성자, 날짜, 걸린 글, 본문). 번호를 주면 그 메모가 걸린 글로 화면을 옮긴다
 *   node cli.mjs memos add <p12|T1r2c1> <본문> [--at 걸 글] [--author 이름]   메모 달기(--at 없으면 문단 전체, 작성자 기본 Claude)
 *   node cli.mjs memos edit <번호> <본문>   메모 본문 고치기       node cli.mjs memos del <번호>   메모 지우기(걸린 글은 남음)
 *   node cli.mjs inspect | slots       행정문서 표기 검수 / 아직 안 채운 칸
 *   node cli.mjs tools                 편집 도구 25종 정의(이름, 설명, 인자)
 *   node cli.mjs changes [--all]       아직 안 읽은 사용자 수정 내역 (읽으면 읽음 처리)
 *   node cli.mjs save [출력.hwpx]      새 판으로 저장 (기본: <이름>_<YYMMDD>_<NN>.hwpx, 덮어쓰기 없음)
 *   node cli.mjs undo                  마지막 배치 되돌리기
 *   node cli.mjs log [N | --all]       작업 기록(시작, 불러옴, 편집, 화면 저장 포함 저장, 종료, 오류). 비우지 않고 쌓인다
 *   node cli.mjs list                  떠 있는 에디터 전부(세션마다 하나. * 는 이 세션의 것)
 *   node cli.mjs url                   이 인스턴스 서버의 주소(떠 있고 이 인스턴스 것일 때만). 브라우저 자동화는 이 주소로만 연다
 *   node cli.mjs status | stop
 */
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import net from 'node:net';
import { spawn, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { readZip, fixHfFields } from './hwpx-zip.mjs';
import { formatLog, formatOp, coalesceOps, localTime } from './log-format.mjs';
import { restoreImages } from './image-proxy.mjs';

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

/**
 * start 때 7일 넘게 쓰지 않은 다른 인스턴스 폴더를 지운다(세션마다 폴더가 생겨 2026-10-08 130개 9.3GB 가 쌓였다).
 * 서버가 살아 있는 폴더는 남긴다. 폴더 이름에 한글이 올 수 있어 fs.rmSync 대신 파일 단위로 지운다(Node 24 함정).
 */
async function pruneStale() {
  const rmrf = (p) => {
    if (fs.lstatSync(p).isDirectory()) { for (const n of fs.readdirSync(p)) rmrf(path.join(p, n)); fs.rmdirSync(p); } else fs.unlinkSync(p);
  };
  const limit = Date.now() - 7 * 24 * 3600 * 1000;
  for (const d of fs.readdirSync(ROOT, { withFileTypes: true })) {
    const dir = path.join(ROOT, d.name);
    if (!d.isDirectory() || d.name === 'webview' || path.resolve(dir) === path.resolve(STATE_DIR)) continue;
    try {
      const last = Math.max(fs.statSync(dir).mtimeMs, ...fs.readdirSync(dir).map((n) => fs.statSync(path.join(dir, n)).mtimeMs));
      if (last > limit) continue;
      const port = readPort(dir);
      if (port && path.resolve((await probe(port))?.stateDir || '') === path.resolve(dir)) continue;
      rmrf(dir);
    } catch { /* 다른 프로세스가 쥐고 있으면 다음 start 때 다시 본다 */ }
  }
}

/** 응답한 서버가 이 인스턴스의 것인가(같은 포트를 다른 인스턴스가 쥐고 있을 수 있다). */
const ours = (h) => Boolean(h) && path.resolve(h.stateDir || '') === path.resolve(STATE_DIR);

/** start 가 쓸 포트: 이 인스턴스 서버가 살아 있으면 그 포트, 아니면 7780 부터 비어 있는 포트. */
async function allocatePort() {
  const mine = readPort(STATE_DIR);
  if (mine && ours(await probe(mine))) return mine;
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
/** PNG, JPEG, GIF, BMP 머리에서 픽셀 크기를 읽는다. */
function imageSize(b) {
  if (b.length > 24 && b.readUInt32BE(0) === 0x89504e47) return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
  if (b.length > 10 && b.toString('latin1', 0, 3) === 'GIF') return { w: b.readUInt16LE(6), h: b.readUInt16LE(8) };
  if (b.length > 26 && b.toString('latin1', 0, 2) === 'BM') return { w: b.readInt32LE(18), h: Math.abs(b.readInt32LE(22)) };
  if (b[0] === 0xff && b[1] === 0xd8) {
    for (let i = 2; i + 9 < b.length;) {
      if (b[i] !== 0xff) { i++; continue; }
      const marker = b[i + 1];
      const len = b.readUInt16BE(i + 2);
      if (marker >= 0xc0 && marker <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(marker)) return { w: b.readUInt16BE(i + 7), h: b.readUInt16BE(i + 5) };
      i += 2 + len;
    }
  }
  return null;
}
const SEEN = path.join(STATE_DIR, 'changes.seen');
const OPS = path.join(STATE_DIR, 'ops.jsonl');
const OPS_SEEN = path.join(STATE_DIR, 'ops.seen');
const APP_PID = path.join(STATE_DIR, 'app.pid');

const out = (obj) => process.stdout.write((typeof obj === 'string' ? obj : JSON.stringify(obj, null, 2)) + '\n');
// 에디터 서버에 POST 를 보낸 뒤 process.exit() 를 부르면 Windows Node 24 가 libuv 단언
// (`!(handle->flags & UV_HANDLE_CLOSING)`, async.c)으로 죽어 종료 코드가 127 이 됐다(2026-09-28, stop 이 저장 안 한 편집을 알릴 때).
// 그래서 종료 코드만 정하고 예외로 흐름을 끊어, 프로세스가 스스로 끝나게 둔다.
class Die extends Error {}
const die = (msg) => { process.stderr.write(msg + '\n'); process.exitCode = 1; throw new Die(msg); };
const onFatal = (e) => { if (!(e instanceof Die)) { process.stderr.write(String(e?.stack ?? e) + '\n'); process.exitCode = 1; } };
process.on('uncaughtException', onFatal);
process.on('unhandledRejection', onFatal);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// 그 포트의 서버가 다른 인스턴스 것이면 멈춘다. stop 이 포트 파일을 지운 인스턴스에 다시 stop, save 를 내리면 기본 포트 7780 으로
// 가서 남의 에디터 서버를 내리고 그 문서를 내보냈다(2026-10-02, 교육력제고 창의 서버를 내렸다)
if (process.argv[2] && !['start', 'list', 'hold'].includes(process.argv[2])) {
  const h = await probe(PORT);
  if (h?.stateDir && path.resolve(h.stateDir) !== path.resolve(STATE_DIR)) {
    if (process.argv[2] === 'stop') {
      out(`이 인스턴스(${path.basename(STATE_DIR)})의 서버는 떠 있지 않다. 포트 ${PORT} 는 다른 에디터(${path.basename(h.stateDir)})다`);
      throw new Die('');
    }
    die(`포트 ${PORT} 는 다른 에디터(${path.basename(h.stateDir)})다. 이 인스턴스(${path.basename(STATE_DIR)})는 떠 있지 않다 — start 로 연다`);
  }
}

async function health() {
  try { return await (await fetch(`${BASE}/api/health`)).json(); } catch { return null; }
}

/** 작업 기록(editor-log.jsonl)에 한 줄. 서버가 없으면 조용히 넘어간다. */
async function postLog(ev, data = {}) {
  try { await fetch(`${BASE}/api/log`, { method: 'POST', body: JSON.stringify({ ev, ...data }) }); } catch { /* 서버 꺼짐 */ }
}

const LOG = path.join(STATE_DIR, 'editor-log.jsonl');

async function cmd(body) {
  const res = await fetch(`${BASE}/api/cmd`, { method: 'POST', body: JSON.stringify(body) });
  const r = await res.json();
  if (!r.ok) die(`실패: ${r.error}`);
  return r;
}

async function ensureServer() {
  if (ours(await health())) return;
  if (!fs.existsSync(path.join(HERE, 'studio-dist', 'index.html'))) die('studio-dist 가 없다. 먼저 node setup.mjs 로 빌드한다.');
  // 두 start 가 동시에 같은 빈 포트를 고르면 한쪽 서버만 뜬다. 진 쪽은 포트를 다시 골라 띄운다(2026-10-08)
  for (let attempt = 0; attempt < 5; attempt++) {
    const child = spawn(process.execPath, [path.join(HERE, 'server.mjs')], {
      detached: true, stdio: 'ignore', windowsHide: true,
      env: { ...process.env, HWPX_EDITOR_PORT: String(PORT), HWPX_EDITOR_STATE: STATE_DIR },
    });
    child.unref();
    fs.writeFileSync(path.join(STATE_DIR, 'port'), String(PORT));
    let h = null;
    for (let i = 0; i < 50 && !h; i++) { h = await health(); if (!h) await sleep(200); }
    if (ours(h)) return;
    if (!h || process.env.HWPX_EDITOR_PORT) break;
    PORT = await allocatePort(); BASE = `http://127.0.0.1:${PORT}`;
  }
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
  // 주소에 인스턴스 이름을 달아, 포트를 물려받은 다른 인스턴스의 서버에 붙지 않게 한다(2026-10-21)
  const appUrl = `${url}${url.includes('?') ? '&' : '?'}client=app&inst=${encodeURIComponent(path.basename(STATE_DIR))}`;
  const child = spawn(py, [path.join(HERE, 'app.py'), appUrl, title], { detached: true, stdio: 'ignore', env: { ...process.env, HWPX_EDITOR_STATE: STATE_DIR } });
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

/**
 * 에디터를 어디에 열까. --app / --preview / --browser 또는 HWPX_EDITOR_MODE 가 먼저다.
 * 없으면 Claude Code 터미널(CLAUDE_CODE_ENTRYPOINT=cli)이나 사람이 직접 실행한 경우 앱 창,
 * 그 밖(데스크탑 앱 등)은 미리보기. 데스크탑 앱의 CLAUDE_CODE_ENTRYPOINT 값은 공식 문서에 없어 cli 가 아닌 것으로 가른다.
 */
function openMode(args) {
  for (const m of ['app', 'preview', 'browser']) if (args.includes(`--${m}`)) return m;
  if (['app', 'preview', 'browser'].includes(process.env.HWPX_EDITOR_MODE)) return process.env.HWPX_EDITOR_MODE;
  const entry = process.env.CLAUDE_CODE_ENTRYPOINT;
  return !entry || entry === 'cli' ? 'app' : 'preview';
}

/**
 * 데스크탑 앱 미리보기 항목을 작업 폴더의 .claude/launch.json 에 넣는다(다른 항목은 그대로).
 * 미리보기가 실행하는 것은 `cli.mjs hold <상태 폴더>` — 이미 떠 있는 이 에디터 서버에 붙어 있기만 하므로
 * 서버가 둘로 늘지 않는다. 서버가 없으면 hold 가 띄운다.
 */
function registerPreview(url) {
  const dir = path.join(process.cwd(), '.claude');
  const file = path.join(dir, 'launch.json');
  let cfg = { version: '0.0.1', configurations: [] };
  try { cfg = JSON.parse(fs.readFileSync(file, 'utf8')); } catch { /* 없거나 깨졌으면 새로 */ }
  cfg.version ||= '0.0.1';
  cfg.configurations = (cfg.configurations || []).filter((c) => c?.name !== 'hwpx-editor');
  cfg.configurations.push({
    name: 'hwpx-editor',
    runtimeExecutable: process.execPath,
    runtimeArgs: [path.join(HERE, 'cli.mjs'), 'hold', STATE_DIR],
    port: PORT,
    url,
  });
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(file, JSON.stringify(cfg, null, 2) + '\n');
  return file;
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
    // 문서를 주지 않으면 빈 문서(blank.hwpx)를 작업 폴더에 「새 문서.hwpx」로 복사해 연다(이름이 있으면 번호를 붙인다)
    const given = args.find((a) => !a.startsWith('--'));
    let file = given && path.resolve(given);
    if (!given) {
      for (let n = 1; ; n++) {
        file = path.join(process.cwd(), n === 1 ? '새 문서.hwpx' : `새 문서 (${n}).hwpx`);
        if (!fs.existsSync(file)) break;
      }
      fs.copyFileSync(path.join(HERE, 'blank.hwpx'), file);
    }
    // 마크다운 원고를 주면 빌더로 hwpx 를 만들어 연다(같은 이름 .hwpx). --theme, --accent, --light, --font, --design 을 주면
    // 디자인 판(md2hwpx_design: 배너, 절 띠, 표 머리 색), 아니면 md2hwpx(--template 으로 템플릿). 만든 파일이 있으면 --rebuild 로만 다시 만든다
    if (file && /\.md$/i.test(file) && fs.existsSync(file)) {
      const opt = (k) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : null; };
      const design = ['--theme', '--accent', '--light', '--font', '--design'].some((k) => args.includes(k));
      const built = file.replace(/\.md$/i, '.hwpx');
      if (fs.existsSync(built) && !args.includes('--rebuild')) die(`이미 있는 파일: ${built} — 그 파일을 열거나, md 로 다시 만들려면 --rebuild`);
      const extra = design
        ? [...['--theme', '--accent', '--light', '--font'].flatMap((k) => (opt(k) ? [k, opt(k)] : [])), ...(args.includes('--no-layout') ? ['--no-layout'] : [])]
        : (opt('--template') ? ['--template', opt('--template')] : []);
      const script = path.join(HERE, '..', 'scripts', design ? 'md2hwpx_design.py' : 'md2hwpx.py');
      const py = process.platform === 'win32' ? 'python' : 'python3';
      const r = spawnSync(py, [script, file, '-o', built, ...extra], { encoding: 'utf8', windowsHide: true, env: { ...process.env, PYTHONIOENCODING: 'utf-8' } });
      if (r.status !== 0 || !fs.existsSync(built)) die(`md 변환 실패: ${(r.stderr || r.stdout || '').slice(-800)}`);
      out(`md → ${path.basename(built)} (${design ? 'md2hwpx_design' : 'md2hwpx'})`);
      file = built;
    }
    if (!file || !fs.existsSync(file)) die('사용법: start [문서.hwpx|.hwp|원고.md] — 문서를 빼면 빈 문서로 연다');
    const blocker = editBlocker(file);
    if (blocker && !args.includes('--force')) die(`열지 않음: ${blocker}. 사용자가 원하면 --force`);
    if (!process.env.HWPX_EDITOR_PORT) { PORT = await allocatePort(); BASE = `http://127.0.0.1:${PORT}`; }
    else {
      // 포트를 정해 주었는데 그 포트에 다른 에디터가 떠 있으면 그 서버에 묻거나 열지 않고 멈춘다(2026-10-18: 시험용으로 7781 을 정해
      // 띄웠는데 다른 세션의 문항3 에디터가 그 포트에 있었고, 브라우저를 그 주소로 열어 남의 창을 만졌다)
      const h = await health();
      if (h?.stateDir && !ours(h)) {
        die(`포트 ${PORT} 는 다른 에디터(${path.basename(h.stateDir)}, ${h.session?.source ? path.basename(h.session.source) : '문서 없음'})가 쓰고 있다. HWPX_EDITOR_PORT 를 빼면 빈 포트를 고른다`);
      }
    }
    // 빌드 끝에 자동으로 열 때 떠 있는 창의 저장 안 한 편집을 덮지 않는다(세션 파일을 바꾸기 전에 본다)
    const shown = (await health())?.browser;
    if (shown && !args.includes('--force')) {
      let dirty = false;
      try {
        const r = await (await fetch(`${BASE}/api/cmd`, { method: 'POST', body: JSON.stringify({ type: 'state', timeoutMs: 5000 }) })).json();
        dirty = Boolean(r.ok && r.state?.dirty);
      } catch { /* 창이 응답하지 않으면 연다 */ }
      if (dirty) die('에디터에 저장하지 않은 편집이 있다. 사용자에게 저장을 부탁하거나, 버리려면 start --force');
    }
    if (shown) {
      // 떠 있는 문서를 고치려고 다시 빌드해 같은 문서(같은 파일, 같은 이름의 다른 판)를 다시 여는 것을 막는다(2026-10-17 사용자 지적)
      let open;
      try { open = JSON.parse(fs.readFileSync(SESSION, 'utf8')).source; } catch { /* 열린 문서 기록 없음 */ }
      const stem = (f) => path.basename(f, path.extname(f)).replace(/_\d{6}_\d{2}$/, '').normalize('NFC');
      const reopenArg = args.find((a) => a === '--reopen' || a.startsWith('--reopen='));
      const reason = reopenArg?.includes('=') ? reopenArg.slice('--reopen='.length).trim() : '';
      const same = open && (path.resolve(open) === file || stem(open) === stem(file));
      if (same && !reopenArg) {
        die(`열지 않음: 같은 문서가 이미 에디터에 떠 있다(${path.basename(open)}).\n`
          + `고치는 일이면 다시 빌드하거나 새로 열지 말고 cli.mjs run 으로 에디터 위에서 고친다(editor-mode.md 「대화 규칙」).\n`
          + `사용자가 다시 열라고 했거나 저장본을 정본으로 다시 빌드한 경우에만 start --reopen`);
      }
      // 같은 이름의 다른 판(빌드 스크립트가 새로 만든 _NN)은 사유 없이 다시 열지 않는다. 편집 요청마다 다시 빌드하고
      // --reopen 으로 열어 열네 판을 갈아 끼우고 사용자 편집까지 버린 일이 있었다(2026-10-21 사용자 지적)
      if (same && path.resolve(open) !== file && !reason) {
        die(`열지 않음: 떠 있는 문서(${path.basename(open)})의 다른 판(${path.basename(file)})이다.\n`
          + `편집 요청을 반영하려는 것이면 다시 빌드하지 말고 cli.mjs run 으로 떠 있는 문서를 고친다.\n`
          + `다른 판을 꼭 열어야 하면 사유를 적는다: --reopen="사용자 요청" 또는 --reopen="저장본 기준 다시 빌드"`);
      }
      if (same) await postLog('reopen', { from: path.basename(open), to: path.basename(file), reason: reason || '같은 파일 다시 열기' });
    }
    fs.mkdirSync(STATE_DIR, { recursive: true });
    fs.writeFileSync(SESSION, JSON.stringify({ source: file, startedAt: new Date().toISOString() }, null, 2));
    fs.writeFileSync(CHANGES, '');
    fs.writeFileSync(SEEN, '0');
    // 실시간 편집 기록은 비우지 않고 쌓는다(에디터 「로그」 패널이 지난 기록도 보인다). 최근 5000줄만 남기고,
    // 열림 구분 줄을 넣은 뒤 읽은 자리를 끝으로 옮겨 changes 는 지금부터의 편집만 보인다.
    const kept = readOps().slice(-5000);
    kept.push({ t: Date.now(), act: 'mark', type: 'open', src: 'system', label: `── 열림 ${path.basename(file)}` });
    fs.writeFileSync(OPS, kept.map((o) => JSON.stringify(o)).join('\n') + '\n');
    fs.writeFileSync(OPS_SEEN, String(kept.length));
    await ensureServer();
    await pruneStale();
    await postLog('start', { file, instance: path.basename(STATE_DIR), port: PORT });
    let h = await health();
    const mode = openMode(args);
    // 옛 앱 창이 새 서버에 다시 붙기를 기다린다. 앱 모드에서는 앱 창(h.app)을 기다린다 — 다른 화면이 먼저 붙었다고
    // 건너뛰면 앱 창이 없다고 보고 하나 더 띄워 창이 쌓였다(2026-10-21 사용자 지적)
    const attached = (x) => (mode === 'app' ? x.app : x.browser);
    if (!attached(h) && aliveAppPid()) {
      for (let i = 0; i < 20 && !attached(h); i++) { await sleep(500); h = await health(); }
    }
    // 이미 열린 화면이 있으면 그 화면에 새 문서를 연다. 다만 앱 모드(터미널 기본, --app)에서는 앱 창만 다시 쓴다.
    // 예전에 열어 둔 브라우저 탭이 서버에 붙어 있다고 앱 창 대신 그 탭에 열던 것을 막는다(2026-10-21 사용자 지적).
    // 앱 창이 뜨면 서버가 그 탭에 yield 를 보내 물러나게 한다
    if (h.browser && (mode !== 'app' || h.app)) await cmd({ type: 'open' });
    else if (mode === 'preview') {
      // 데스크탑 앱: 창을 띄우지 않고 앱 내장 브라우저(미리보기)가 열 항목을 .claude/launch.json 에 둔다
      const where = registerPreview(`http://localhost:${PORT}/`);
      out(`에디터: http://localhost:${PORT}/\n미리보기: ${where} 의 "hwpx-editor" — 데스크탑 앱 미리보기 창에서 연다(문서는 그때 열린다)`);
      process.exit(0);
    } else if (!args.includes('--no-browser')) {
      const url = `http://localhost:${PORT}/`;
      // 기본은 앱 창(한/글 단축키 전부). --browser 면 브라우저 탭(Ctrl+N 계열은 Ctrl+M 으로 대신).
      if (mode !== 'browser') {                        // 다시 붙지 않은 옛 앱 창은 닫는다(창 하나만 쓴다)
        const old = aliveAppPid();
        if (old) { try { process.kill(old); } catch { /* 이미 닫힘 */ } }
      }
      if (mode === 'browser' || !openAppWindow(url, path.basename(file))) openBrowser(url);
    }
    // 스킬 파이프라인 산출물은 서버가 rhwp 로 표 높이를 재서 보내므로(rhwp_layout.mjs) 넉넉히 기다린다.
    for (let i = 0; i < 180; i++) {
      if (readChanges().some((c) => c.source === 'open')) { out(`열림: ${file}\n에디터: http://localhost:${PORT}/`); process.exit(0); }
      await sleep(500);
    }
    die('브라우저에서 문서가 열리지 않았다(90초). 탭을 확인한다.');
    break;
  }
  case 'hold': {
    // 데스크탑 앱 미리보기가 실행한다(registerPreview). 인자로 받은 에디터의 서버에 붙어 있고, 서버가 내려가면 끝난다.
    if (args[0]) { STATE_DIR = path.resolve(args[0]); PORT = readPort(STATE_DIR) || PORT; BASE = `http://127.0.0.1:${PORT}`; }
    if (!fs.existsSync(path.join(STATE_DIR, 'session.json'))) die('열린 문서가 없다. 먼저 start <문서>');
    await ensureServer();
    out(`에디터 서버: http://localhost:${PORT}/`);
    while (await health()) await sleep(2000);
    break;
  }
  case 'run': {
    const src = args[0] === '-' || !args[0] ? fs.readFileSync(0, 'utf8') : fs.readFileSync(args[0], 'utf8');
    // KS X 6101 §5.3: 본문은 NFC. 맥, 웹에서 온 NFD(자모 분리) 글자는 검색과 치환을 조용히 깨뜨린다.
    const ops = JSON.parse(src, (k, v) => (typeof v === 'string' ? v.normalize('NFC') : v));
    out((await cmd({ type: 'run', ops: Array.isArray(ops) ? ops : [ops] })).result);
    break;
  }
  case 'image': {
    // 그림 넣기: image <그림 파일> [좌표] [--end] [--replace] [--width mm] [--desc 설명]. 자리를 안 주면 사용자 커서
    const file = args[0];
    if (!file || !fs.existsSync(file)) die('image <그림 파일> [좌표] [--end] [--replace] [--width mm] [--desc 설명] [--wrap square|topbottom|behind|front [--align left|center|right] [--x mm] [--y mm] [--page]]');
    const buf = fs.readFileSync(file);
    const ext = path.extname(file).slice(1).toLowerCase();
    const size = imageSize(buf);
    if (!size) die(`그림 크기를 못 읽음(PNG, JPEG, GIF, BMP 만): ${file}`);
    const opt = (name) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : undefined; };
    const valued = ['--width', '--desc', '--wrap', '--align', '--x', '--y'];
    const at = args.slice(1).find((a, i, arr) => !a.startsWith('--') && !valued.includes(arr[i - 1]));
    // 글 배치(--wrap square|topbottom|behind|front)를 주면 글자처럼 취급하지 않는 그림으로 넣는다(본문만). 사용자 요청 2026-10-19
    const wrap = opt('--wrap');
    if (wrap && !['square', 'topbottom', 'behind', 'front'].includes(wrap)) die('--wrap 은 square(어울림), topbottom(자리 차지), behind(글 뒤로), front(글 앞으로) 가운데 하나');
    const align = opt('--align');
    if (align && !['left', 'center', 'right'].includes(align)) die('--align 은 left, center, right 가운데 하나');
    const image = { base64: buf.toString('base64'), ext: ext === 'jpeg' ? 'jpg' : ext, naturalW: size.w, naturalH: size.h,
      at, end: args.includes('--end'), replace: args.includes('--replace'), widthMm: opt('--width') ? Number(opt('--width')) : undefined, desc: opt('--desc'),
      wrap, align, xMm: opt('--x') ? Number(opt('--x')) : undefined, yMm: opt('--y') ? Number(opt('--y')) : undefined, page: args.includes('--page') };
    out((await cmd({ type: 'run', ops: [{ image }] })).result);
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
  case 'memos': {
    // 문서에 달린 메모(검토 의견). 번호는 문서 순서이고 에디터 메모 패널의 번호와 같다
    // add <좌표> <본문> [--at 걸 글] [--author 이름] | edit <번호> <본문> | del <번호>. 본문의 \n 은 줄바꿈(줄마다 메모 문단 하나)
    const [act, a1, a2] = args;
    if (['add', 'edit', 'del'].includes(act)) {
      const opt = (k) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : undefined; };
      const body = (s) => String(s ?? '').normalize('NFC').replace(/\\n/g, '\n');
      if (!a1 || (act !== 'del' && a2 == null)) die('사용: memos add <p12|T1r2c1|T1r2c1/T1r0c0> <본문> [--at 걸 글] [--author 이름] | memos edit <번호> <본문> | memos del <번호>');
      const op = act === 'add'
        ? { action: 'add', ref: a1, text: body(a2), at: opt('--at') && body(opt('--at')), author: opt('--author') }
        : { action: act, text: act === 'edit' ? body(a2) : undefined };
      await cmd({ type: 'memos', n: act === 'add' ? undefined : Number(a1), op });
      out(act === 'add' ? `메모를 달았다: ${a1}` : act === 'edit' ? `메모 ${a1} 본문을 고쳤다` : `메모 ${a1} 을 지웠다(걸린 글은 남음, undo 로 되돌림)`);
      break;
    }
    const n = args.find((a) => /^\d+$/.test(a));
    if (n) { out((await cmd({ type: 'memos', n: Number(n) })).result ? `이동: 메모 ${n}` : `못 찾음: 메모 ${n}`); break; }
    const list = (await cmd({ type: 'memos' })).result ?? [];
    if (args.includes('--json')) { out(list); break; }
    out(list.length ? [`메모 ${list.length}개`, ...list.map((m) => [
      `[${m.n}] ${m.where}${m.page ? ` ${m.page}쪽` : ''} · ${m.author || '작성자 없음'}${m.when ? ` · ${m.when}` : ''}`,
      `    걸린 글: ${m.anchor.trim() ? `「${m.anchor.replace(/\s+/g, ' ').trim()}」` : '(글 없음)'}`,
      `    메모: ${(m.text || '(본문 없음)').replace(/\n/g, '\n          ')}`,
    ].join('\n'))].join('\n') : '메모 없음');
    break;
  }
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
    let img = null;
    if (s.proxyMap) {                               // 그림 축소 보기로 열었으면 원본 그림으로 되돌려 저장한다
      img = restoreImages(fix.buf, s.proxyMap);
      fix.buf = img.buf;
      out(`그림 원본 복원 ${img.restored}/${img.total}`);
    }
    fs.writeFileSync(target, fix.buf);
    if (fix.fixed) out(`머리말/꼬리말 쪽 번호 ${fix.fixed}개 보정`);
    for (const why of fix.skipped) out(`⚠ 쪽 번호 보정 못 함: ${why}`);
    await cmd({ type: 'saved', fileName: path.basename(target) });
    // 새 판(_NN)으로 저장했으면 화면 저장(Ctrl+S)과 다시 열기도 새 판을 쓰게 연결을 옮긴다. 종전에는 처음 연 파일에
    // 묶여 있어 판을 올릴 때마다 start 로 다시 열어야 했다(2026-10-02 가이드북 세션, 사용자 선택 「새 판으로」).
    // 경로를 준 저장은 내보내기로 보고 연결을 그대로 둔다
    if (!args[0]) fs.writeFileSync(SESSION, JSON.stringify({ ...JSON.parse(fs.readFileSync(SESSION, 'utf8')), source: target }, null, 2));
    await postLog('save', { by: 'claude', path: target, bytes: fix.buf.length, hfFixed: fix.fixed || undefined, imagesRestored: img?.restored });
    out(`저장: ${target}${args[0] ? '' : ' — 화면 Ctrl+S 도 이제 이 파일에 저장한다'}`);
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
  case 'url': {                                     // 이 인스턴스 서버의 주소. 브라우저 자동화는 이 주소로만 연다(포트를 짐작하지 않는다)
    if (!ours(await health())) die(`이 인스턴스(${path.basename(STATE_DIR)})의 서버가 떠 있지 않다 — start 로 연다`);
    out(`${BASE}/`);
    break;
  }
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
  case 'builder': {
    // 에디터에 열린 문서를 빌더 스크립트(scripts/*.py)로 처리하고 결과를 새 판으로 다시 연다 — 에디터에서 빌더 기능(차트, 도장, 메모 만들기,
    // 문서 합치기, 표 칸 수식, 스타일 조건 치환 등)을 쓰는 다리. 인자 안의 {in} 은 지금 화면 문서(저장 안 한 편집 포함)를 꺼낸 파일,
    // {out} 은 결과 파일(원본 옆 새 판 <이름>_<YYMMDD>_<NN>.hwpx)로 바뀐다. 다시 열면 그 앞의 되돌리기(Ctrl+Z) 기록은 끊긴다 —
    // 처리 직전 상태는 상태 폴더에 남겨 두고 `builder --undo` 가 그것을 새 판으로 다시 연다.
    //   builder chart_hwpx {in} {out} --type bar --data data.json      builder seal_hwpx {in} {out} --image 도장.png
    //   builder add_review_memo {in} {out} --memos 메모.json             builder --undo
    const s = JSON.parse(fs.readFileSync(SESSION, 'utf8'));
    if (args[0] === '--undo') {
      const u = s.builderUndo;
      if (!u || !fs.existsSync(u.before)) die('되돌릴 빌더 처리가 없다');
      const target = nextVersion(u.source);
      fs.copyFileSync(u.before, target);
      fs.writeFileSync(SESSION, JSON.stringify({ ...s, source: target, builderUndo: null }, null, 2));
      await cmd({ type: 'open' });
      await postLog('builder', { undo: true, path: target });
      out(`되돌림: 빌더 처리 직전 상태를 새 판으로 열었다 — ${target}`);
      break;
    }
    const [name, ...rest] = args;
    if (!name) die('사용법: builder <스크립트 이름|경로.py> <인자… {in} … {out} …> | builder --undo');
    const scriptsDir = path.join(HERE, '..', 'scripts');
    const script = fs.existsSync(name) ? path.resolve(name) : path.join(scriptsDir, name.endsWith('.py') ? name : `${name}.py`);
    if (!fs.existsSync(script)) die(`빌더 스크립트가 없다: ${script}\n있는 것: ${fs.readdirSync(scriptsDir).filter((f) => f.endsWith('.py')).join(', ')}`);
    if (!rest.some((a) => a.includes('{in}')) || !rest.some((a) => a.includes('{out}'))) {
      die('인자에 {in}(지금 문서)과 {out}(결과)을 넣는다. 스크립트마다 자리가 다르다: 예) chart_hwpx {in} {out} …, add_equation {in} --output {out} …');
    }
    if (!/\.hwpx$/i.test(s.source || '')) die('hwpx 문서에서만 쓴다(hwp 는 먼저 hwpx 로 저장)');
    const dir = path.join(STATE_DIR, 'builder');
    fs.mkdirSync(dir, { recursive: true });
    const before = path.join(dir, `before_${Date.now()}.hwpx`);
    const r = await cmd({ type: 'save' });
    const fix = fixHfFields(Buffer.from(r.base64, 'base64'), r.hfMarkers ?? []);
    if (s.proxyMap) fix.buf = restoreImages(fix.buf, s.proxyMap).buf;   // 그림 축소 보기면 원본 그림으로 넘긴다
    fs.writeFileSync(before, fix.buf);
    const result = nextVersion(s.source);
    const argv = rest.map((a) => a.replaceAll('{in}', before).replaceAll('{out}', result));
    const py = process.platform === 'win32' ? 'python' : 'python3';
    const run = spawnSync(py, [script, ...argv], { encoding: 'utf8', windowsHide: true, cwd: process.cwd(), env: { ...process.env, PYTHONIOENCODING: 'utf-8' } });
    if (run.stdout?.trim()) out(run.stdout.trim().split('\n').slice(-20).join('\n'));
    if (run.status !== 0 || !fs.existsSync(result)) {
      die(`빌더 실패(에디터 문서는 그대로): ${path.basename(script)} 종료 ${run.status}\n${(run.stderr || '').trim().split('\n').slice(-15).join('\n')}`);
    }
    fs.writeFileSync(SESSION, JSON.stringify({ ...s, source: result, proxyMap: null, builderUndo: { before, source: s.source } }, null, 2));
    await cmd({ type: 'open' });
    await postLog('builder', { script: path.basename(script), args: rest.join(' ').slice(0, 300), path: result });
    out(`빌더 적용: ${path.basename(script)} → 새 판 ${result}\n화면 저장(Ctrl+S)도 이 파일에 저장한다. 되돌리려면 builder --undo`);
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
  default: out(fs.readFileSync(fileURLToPath(import.meta.url), 'utf8').split('\n').slice(2, 18).join('\n'));
}
