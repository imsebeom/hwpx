#!/usr/bin/env node
/**
 * hwpx 에디터 브리지 서버. 의존성 없음(Node 18+).
 *
 *   터미널 Claude ──(cli.mjs, HTTP)──▶ 이 서버 ◀──(long-poll)── 브라우저 호스트 페이지 ─▶ rhwp-studio iframe
 *
 * - /studio/  : setup.mjs 가 빌드한 rhwp-studio (claude 플러그인 포함)
 * - /sdk/     : @rhwp/editor SDK
 * - /         : 호스트 페이지(host/)
 * - /api/cmd  : CLI 가 명령을 넣고 브라우저의 결과를 기다린다
 * - /api/poll, /api/result : 브라우저가 명령을 받아 가고 결과를 돌려준다
 * - /api/snapshot : 브라우저가 문서가 바뀔 때마다 hwpx 와 본문 텍스트를 올린다
 *
 * 작업 공간(STATE_DIR): latest.hwpx(항상 최신), changes.jsonl(수정 내역), session.json
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { stripDummyLinesegs } from './hwpx-zip.mjs';

const execFileP = promisify(execFile);

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.HWPX_EDITOR_PORT || 7780);
export const STATE_DIR = process.env.HWPX_EDITOR_STATE || path.join(os.homedir(), '.claude', 'cache', 'hwpx-editor');
fs.mkdirSync(STATE_DIR, { recursive: true });

const STATIC = [
  ['/studio/', path.join(HERE, 'studio-dist')],
  ['/sdk/', path.join(HERE, 'sdk')],
  ['/', path.join(HERE, 'host')],
];
const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.json': 'application/json', '.wasm': 'application/wasm', '.svg': 'image/svg+xml',
  '.png': 'image/png', '.ico': 'image/x-icon', '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf',
  '.webmanifest': 'application/manifest+json', '.hwp': 'application/octet-stream', '.hwpx': 'application/octet-stream',
};

// ── 명령 큐 ───────────────────────────────────────────────
let nextId = 1;
const queue = [];              // 브라우저가 아직 안 가져간 명령
const waiting = new Map();     // id → { resolve, timer }  (CLI 가 결과를 기다리는 중)
let pollers = [];              // 대기 중인 브라우저 long-poll 응답
let lastPollAt = 0;

function dispatch() {
  while (queue.length && pollers.length) {
    const res = pollers.shift();
    sendJson(res, 200, queue.shift());
  }
}

function enqueue(cmd, timeoutMs) {
  const id = nextId++;
  return new Promise((resolve) => {
    const timer = setTimeout(() => {
      waiting.delete(id);
      const i = queue.findIndex((c) => c.id === id);
      if (i >= 0) queue.splice(i, 1);
      resolve({ ok: false, error: `브라우저 응답 없음(${timeoutMs}ms). 에디터 탭이 열려 있는지 확인` });
    }, timeoutMs);
    waiting.set(id, { resolve, timer });
    queue.push({ id, ...cmd });
    dispatch();
  });
}

// ── 스냅샷과 수정 내역 ──────────────────────────────────
const LATEST = path.join(STATE_DIR, 'latest.hwpx');
const LATEST_TXT = path.join(STATE_DIR, 'latest.txt');
const LATEST_MODEL = path.join(STATE_DIR, 'latest.model.json');
const CHANGES = path.join(STATE_DIR, 'changes.jsonl');
const SESSION = path.join(STATE_DIR, 'session.json');

/**
 * 작업 기록(editor-log.jsonl). changes.jsonl 은 start 때마다 비우는 「읽지 않은 편집」 큐이고,
 * 이것은 비우지 않고 쌓는 기록이다 — 세션 시작, 문서 열기(줄 배치 경로), 편집, 저장(화면 저장 포함), 종료, 오류.
 */
const LOG = path.join(STATE_DIR, 'editor-log.jsonl');
export function logEvent(ev, data = {}) {
  try {
    const s = readSession();
    fs.appendFileSync(LOG, JSON.stringify({ ts: new Date().toISOString(), ev, doc: s.source ? path.basename(s.source) : null, ...data }) + '\n');
  } catch { /* 기록 실패가 편집을 막지 않는다 */ }
}

/**
 * 에디터에 보낼 문서 바이트. 스킬 파이프라인 산출물(더미 줄 배치)이면 한글로 줄 배치와 표 높이를 계산해
 * 옮겨 심은 판(hancom_layout.py)을 보낸다. 한글이 없거나 실패하면 더미만 걷어낸다(표가 겹칠 수 있다).
 * 원본 파일은 어느 경우에도 건드리지 않는다. 결과는 원본의 크기와 수정 시각으로 캐시한다.
 */
const LAYOUT_CACHE = path.join(STATE_DIR, 'layout-cache.hwpx');
const LAYOUT_KEY = path.join(STATE_DIR, 'layout-cache.json');
async function editorBytes(src) {
  const raw = fs.readFileSync(src);
  if (!/\.hwpx$/i.test(src)) { logEvent('load', { layout: 'raw' }); return raw; }
  const stripped = stripDummyLinesegs(raw);
  if (!stripped.removed) { logEvent('load', { layout: 'stored' }); return raw; }
  if (process.platform !== 'win32') { logEvent('load', { layout: 'strip', dummy: stripped.removed }); return stripped.buf; }
  const st = fs.statSync(src);
  const key = JSON.stringify({ src, size: st.size, mtimeMs: st.mtimeMs });
  try {
    if (fs.readFileSync(LAYOUT_KEY, 'utf8') === key) { logEvent('load', { layout: 'hancom-cache', dummy: stripped.removed }); return fs.readFileSync(LAYOUT_CACHE); }
  } catch { /* 캐시 없음 */ }
  try {
    await execFileP('python', [path.join(HERE, '..', 'scripts', 'hancom_layout.py'), src, LAYOUT_CACHE],
      { timeout: 120000, windowsHide: true, env: { ...process.env, PYTHONIOENCODING: 'utf-8' } });
    fs.writeFileSync(LAYOUT_KEY, key);
    console.log(`한글 줄 배치 적용: ${path.basename(src)}`);
    logEvent('load', { layout: 'hancom', dummy: stripped.removed });
    return fs.readFileSync(LAYOUT_CACHE);
  } catch (e) {
    const why = String(e?.stderr || e?.message || e).trim().split('\n').pop();
    console.error(`한글 줄 배치 실패, 더미만 걷어냄: ${why}`);
    logEvent('load', { layout: 'strip', dummy: stripped.removed, error: why });
    return stripped.buf;
  }
}

function readSession() {
  try { return JSON.parse(fs.readFileSync(SESSION, 'utf8')); } catch { return {}; }
}
function writeSession(patch) {
  const s = { ...readSession(), ...patch };
  fs.writeFileSync(SESSION, JSON.stringify(s, null, 2));
  return s;
}

/** 줄 단위 diff. 앞뒤 공통 부분을 걷어 내고 가운데만 LCS 로 맞춘다. */
export function lineDiff(a, b) {
  return seqDiff(a.split('\n'), b.split('\n'));
}

/**
 * 글 모델(플러그인 model(): 본문 문단 글, 셀 문단 글, 표 모양) 두 개의 차이를 좌표로.
 * 반환: [{ op: '~'|'+'|'-', ref: 'p12'|'T1r0c1', before?, after? }] — 구역이 여럿이면 null(줄 diff 로)
 */
export function modelDiff(a, b) {
  if (!a || !b || a.sections !== 1 || b.sections !== 1) return null;
  const out = [];
  // 지운 문단과 넣은 문단 가운데 글이 비슷한 것끼리(순서대로) "바뀜"으로 묶는다. 좌표는 새 문서 기준.
  const raw = seqDiff(a.paras, b.paras);
  const dels = raw.filter((d) => d.op === '-'), adds = raw.filter((d) => d.op === '+');
  const used = new Set();
  let from = 0;
  for (const del of dels) {
    const k = adds.findIndex((add, j) => j >= from && !used.has(j) && similar(del.text, add.text) >= 0.3);
    if (k < 0) { out.push({ op: '-', ref: `p${del.line - 1}`, before: del.text }); continue; }
    used.add(k);
    from = k + 1;
    out.push({ op: '~', ref: `p${adds[k].line - 1}`, before: del.text, after: adds[k].text });
  }
  adds.forEach((add, j) => { if (!used.has(j)) out.push({ op: '+', ref: `p${add.line - 1}`, after: add.text }); });
  const cellRef = (k) => (k.endsWith('#0') ? k.slice(0, -2) : k);
  for (const k of new Set([...Object.keys(a.cells), ...Object.keys(b.cells)])) {
    if (a.cells[k] === b.cells[k]) continue;
    if (!(k in a.cells)) out.push({ op: '+', ref: cellRef(k), after: b.cells[k] });
    else if (!(k in b.cells)) out.push({ op: '-', ref: cellRef(k), before: a.cells[k] });
    else out.push({ op: '~', ref: cellRef(k), before: a.cells[k], after: b.cells[k] });
  }
  if (a.shape.replace(/@\d+\.\d+/g, '') !== b.shape.replace(/@\d+\.\d+/g, '')) out.push({ op: '!', ref: '표', after: '표 모양(행, 열, 병합)이 바뀌었다' });
  return out;
}

/** 두 글의 2글자 묶음 겹침(Dice 계수, 0~1). */
function similar(x, y) {
  if (x === y) return 1;
  const grams = (s) => { const m = new Map(); for (let i = 0; i < s.length - 1; i++) { const g = s.slice(i, i + 2); m.set(g, (m.get(g) || 0) + 1); } return m; };
  const gx = grams(x), gy = grams(y);
  let both = 0, total = 0;
  for (const [g, c] of gx) { both += Math.min(c, gy.get(g) || 0); total += c; }
  for (const c of gy.values()) total += c;
  return total ? (2 * both) / total : 0;
}

function seqDiff(A, B) {
  let p = 0;
  while (p < A.length && p < B.length && A[p] === B[p]) p++;
  let s = 0;
  while (s < A.length - p && s < B.length - p && A[A.length - 1 - s] === B[B.length - 1 - s]) s++;
  const a2 = A.slice(p, A.length - s), b2 = B.slice(p, B.length - s);
  const n = a2.length, m = b2.length;
  const out = [];
  if (n * m > 4_000_000) {       // 너무 크면 통째 교체로 본다
    a2.forEach((t, i) => out.push({ op: '-', line: p + i + 1, text: t }));
    b2.forEach((t, j) => out.push({ op: '+', line: p + j + 1, text: t }));
    return out;
  }
  const L = Array.from({ length: n + 1 }, () => new Uint32Array(m + 1));
  for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--)
    L[i][j] = a2[i] === b2[j] ? L[i + 1][j + 1] + 1 : Math.max(L[i + 1][j], L[i][j + 1]);
  let i = 0, j = 0;
  while (i < n || j < m) {
    if (i < n && j < m && a2[i] === b2[j]) { i++; j++; }
    else if (j < m && (i === n || L[i][j + 1] >= L[i + 1][j])) { out.push({ op: '+', line: p + j + 1, text: b2[j] }); j++; }
    else { out.push({ op: '-', line: p + i + 1, text: a2[i] }); i++; }
  }
  return out;
}

function saveSnapshot(body) {
  const bytes = Buffer.from(body.hwpxBase64, 'base64');
  const tmp = LATEST + '.tmp';
  fs.writeFileSync(tmp, bytes);
  fs.renameSync(tmp, LATEST);
  const text = String(body.text ?? '').replace(/\r\n/g, '\n');
  let prev = '';
  try { prev = fs.readFileSync(LATEST_TXT, 'utf8'); } catch { /* 첫 스냅샷 */ }
  fs.writeFileSync(LATEST_TXT, text);
  let prevModel = null;
  try { prevModel = JSON.parse(fs.readFileSync(LATEST_MODEL, 'utf8')); } catch { /* 첫 스냅샷 */ }
  if (body.model) fs.writeFileSync(LATEST_MODEL, JSON.stringify(body.model));
  const entry = {
    ts: new Date().toISOString(),
    source: body.source,           // user | claude | open
    changeSeq: body.changeSeq,
    cursor: body.cursor ?? null,
  };
  if (body.source === 'open') {
    entry.note = '문서 열림';
  } else {
    // 좌표 diff(p12, T1r0c1). 구역이 여럿이거나 모델이 없으면 줄 diff.
    const md = modelDiff(prevModel, body.model);
    entry.diff = md ?? lineDiff(prev, text);
    if (md) entry.coords = true;
    if (!entry.diff.length) entry.formatOnly = true;   // 글자는 그대로, 서식이나 개체만 바뀜
  }
  fs.appendFileSync(CHANGES, JSON.stringify(entry) + '\n');
  if (body.source === 'open') logEvent('open', { bytes: bytes.length });
  else {
    logEvent('edit', {
      by: body.source,
      refs: entry.formatOnly ? [] : entry.diff.slice(0, 12).map((d) => d.ref ?? `줄${d.line}`),
      count: entry.diff.length,
      formatOnly: Boolean(entry.formatOnly),
      at: entry.cursor?.cell?.ref ?? (entry.cursor ? `p${entry.cursor.para}` : null),
    });
  }
  writeSession({ lastSnapshotAt: entry.ts, changeSeq: body.changeSeq, bytes: bytes.length });
  return entry;
}

// ── HTTP ─────────────────────────────────────────────────
function sendJson(res, status, obj) {
  const data = Buffer.from(JSON.stringify(obj));
  res.writeHead(status, { 'content-type': 'application/json; charset=utf-8', 'content-length': data.length, 'cache-control': 'no-store' });
  res.end(data);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', (c) => chunks.push(c));
    req.on('end', () => {
      const raw = Buffer.concat(chunks).toString('utf8');
      try { resolve(raw ? JSON.parse(raw) : {}); } catch (e) { reject(e); }
    });
    req.on('error', reject);
  });
}

function serveStatic(req, res, urlPath) {
  for (const [prefix, dir] of STATIC) {
    if (!urlPath.startsWith(prefix)) continue;
    let rel = decodeURIComponent(urlPath.slice(prefix.length)) || 'index.html';
    if (rel.endsWith('/')) rel += 'index.html';
    const file = path.normalize(path.join(dir, rel));
    if (!file.startsWith(dir)) break;
    if (fs.existsSync(file) && fs.statSync(file).isFile()) {
      res.writeHead(200, { 'content-type': MIME[path.extname(file).toLowerCase()] || 'application/octet-stream', 'cache-control': 'no-cache' });
      fs.createReadStream(file).pipe(res);
      return;
    }
    break;
  }
  res.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' });
  res.end('not found');
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const p = url.pathname;
  try {
    if (p === '/api/log' && req.method === 'POST') {   // 호스트 페이지(화면 저장, 오류)와 CLI(start, save)가 남기는 기록
      const { ev, ...data } = await readBody(req);
      logEvent(String(ev || 'note'), data);
      return sendJson(res, 200, { ok: true });
    }
    if (p === '/api/health') {
      return sendJson(res, 200, { ok: true, pid: process.pid, browser: Date.now() - lastPollAt < 30_000, session: readSession(), stateDir: STATE_DIR });
    }
    if (p === '/api/cmd' && req.method === 'POST') {
      const body = await readBody(req);
      if (body.type === 'shutdown') {
        logEvent('stop');
        sendJson(res, 200, { ok: true });
        setTimeout(() => process.exit(0), 100);
        return;
      }
      const timeoutMs = Number(body.timeoutMs) || 60_000;
      delete body.timeoutMs;
      return sendJson(res, 200, await enqueue(body, timeoutMs));
    }
    if (p === '/api/poll') {
      lastPollAt = Date.now();
      if (queue.length) return sendJson(res, 200, queue.shift());
      pollers.push(res);
      const t = setTimeout(() => {
        pollers = pollers.filter((r) => r !== res);
        sendJson(res, 200, { id: 0, type: 'noop' });
      }, 25_000);
      res.on('close', () => { clearTimeout(t); pollers = pollers.filter((r) => r !== res); });
      return;
    }
    if (p === '/api/result' && req.method === 'POST') {
      const body = await readBody(req);
      const w = waiting.get(body.id);
      if (w) { clearTimeout(w.timer); waiting.delete(body.id); w.resolve(body); }
      return sendJson(res, 200, { ok: true });
    }
    if (p === '/api/snapshot' && req.method === 'POST') {
      const entry = saveSnapshot(await readBody(req));
      return sendJson(res, 200, { ok: true, diffLines: entry.diff?.length ?? 0 });
    }
    if (p === '/api/doc') {       // 브라우저가 처음 열 문서를 받아 간다
      const s = readSession();
      if (!s.source || !fs.existsSync(s.source)) return sendJson(res, 404, { ok: false });
      const buf = await editorBytes(s.source);
      return sendJson(res, 200, { ok: true, fileName: path.basename(s.source), base64: buf.toString('base64') });
    }
    return serveStatic(req, res, p);
  } catch (e) {
    return sendJson(res, 500, { ok: false, error: String(e?.stack || e) });
  }
});

server.listen(PORT, '127.0.0.1', () => {
  fs.writeFileSync(path.join(STATE_DIR, 'server.pid'), String(process.pid));
  console.log(`hwpx 에디터 브리지: http://localhost:${PORT}/  (작업 공간 ${STATE_DIR})`);
});
