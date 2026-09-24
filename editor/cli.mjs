#!/usr/bin/env node
/**
 * Claude 가 쓰는 에디터 조작 CLI.
 *
 *   node cli.mjs start <문서.hwpx>     서버를 띄우고 브라우저에 문서를 연다
 *   node cli.mjs run <ops.json | ->    JSON 명령 배열을 에디터에 적용 (한 트랜잭션, undo 1스텝)
 *   node cli.mjs text                  현재 본문 텍스트
 *   node cli.mjs state                 문서 상태와 사용자 커서 위치
 *   node cli.mjs changes [--all]       아직 안 읽은 사용자 수정 내역 (읽으면 읽음 처리)
 *   node cli.mjs save [출력.hwpx]      새 판으로 저장 (기본: <이름>_<YYMMDD>_<NN>.hwpx, 덮어쓰기 없음)
 *   node cli.mjs undo                  마지막 배치 되돌리기
 *   node cli.mjs status | stop
 */
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { readZip, fixHfFields } from './hwpx-zip.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.HWPX_EDITOR_PORT || 7780);
const BASE = `http://127.0.0.1:${PORT}`;
const STATE_DIR = process.env.HWPX_EDITOR_STATE || path.join(os.homedir(), '.claude', 'cache', 'hwpx-editor');
const SESSION = path.join(STATE_DIR, 'session.json');
const CHANGES = path.join(STATE_DIR, 'changes.jsonl');
const SEEN = path.join(STATE_DIR, 'changes.seen');

const out = (obj) => process.stdout.write((typeof obj === 'string' ? obj : JSON.stringify(obj, null, 2)) + '\n');
const die = (msg) => { process.stderr.write(msg + '\n'); process.exit(1); };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function health() {
  try { return await (await fetch(`${BASE}/api/health`)).json(); } catch { return null; }
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
  const child = spawn(process.execPath, [path.join(HERE, 'server.mjs')], { detached: true, stdio: 'ignore', windowsHide: true });
  child.unref();
  for (let i = 0; i < 50; i++) { if (await health()) return; await sleep(200); }
  die('서버가 뜨지 않았다');
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

function readChanges() {
  try { return fs.readFileSync(CHANGES, 'utf8').split('\n').filter(Boolean).map((l) => JSON.parse(l)); } catch { return []; }
}

function formatChange(c) {
  const head = `[${c.ts.slice(11, 19)}] ${c.source === 'user' ? '사용자' : c.source === 'claude' ? 'Claude' : '열림'}`;
  const sel = c.selection?.paragraph != null ? ` (커서: 문단 ${c.selection.paragraph + 1})` : '';
  if (c.note) return `${head} ${c.note}`;
  if (c.formatOnly) return `${head} 서식이나 개체만 바뀜(글자 변화 없음)${sel}`;
  return [`${head}${sel}`, ...c.diff.map((d) => `  ${d.op}${String(d.line).padStart(4)} │ ${d.text}`)].join('\n');
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
    await ensureServer();
    const h = await health();
    if (h.browser) await cmd({ type: 'open' });       // 이미 열린 탭이 있으면 그 탭에 새 문서를 연다
    else if (!args.includes('--no-browser')) openBrowser(`http://localhost:${PORT}/`);
    for (let i = 0; i < 60; i++) {
      if (readChanges().some((c) => c.source === 'open')) { out(`열림: ${file}\n에디터: http://localhost:${PORT}/`); process.exit(0); }
      await sleep(500);
    }
    die('브라우저에서 문서가 열리지 않았다(30초). 탭을 확인한다.');
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
  case 'state': { const r = await cmd({ type: 'state' }); out({ state: r.state, selection: r.selection, pageCount: r.pageCount }); break; }
  case 'undo': out((await cmd({ type: 'undo' })).result); break;
  case 'changes': {
    const all = readChanges();
    const seen = args.includes('--all') ? 0 : Number(fs.existsSync(SEEN) ? fs.readFileSync(SEEN, 'utf8') : 0);
    const fresh = all.slice(seen).filter((c) => c.source === 'user');
    fs.writeFileSync(SEEN, String(all.length));
    out(fresh.length ? fresh.map(formatChange).join('\n') : '새 사용자 수정 없음');
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
    out(`저장: ${target}`);
    break;
  }
  case 'status': out((await health()) ?? '서버 꺼짐'); break;
  case 'stop': {
    if (await health()) await fetch(`${BASE}/api/cmd`, { method: 'POST', body: JSON.stringify({ type: 'shutdown' }) });
    out('서버 종료');
    break;
  }
  default: out(fs.readFileSync(fileURLToPath(import.meta.url), 'utf8').split('\n').slice(2, 14).join('\n'));
}
