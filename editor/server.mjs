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
const CHANGES = path.join(STATE_DIR, 'changes.jsonl');
const SESSION = path.join(STATE_DIR, 'session.json');

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
  const A = a.split('\n'), B = b.split('\n');
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
  const entry = {
    ts: new Date().toISOString(),
    source: body.source,           // user | claude | open
    changeSeq: body.changeSeq,
    selection: body.selection ?? null,
  };
  if (body.source === 'open') {
    entry.note = '문서 열림';
  } else {
    entry.diff = lineDiff(prev, text);
    if (!entry.diff.length) entry.formatOnly = true;   // 글자는 그대로, 서식이나 개체만 바뀜
  }
  fs.appendFileSync(CHANGES, JSON.stringify(entry) + '\n');
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
    if (p === '/api/health') {
      return sendJson(res, 200, { ok: true, pid: process.pid, browser: Date.now() - lastPollAt < 30_000, session: readSession(), stateDir: STATE_DIR });
    }
    if (p === '/api/cmd' && req.method === 'POST') {
      const body = await readBody(req);
      if (body.type === 'shutdown') {
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
      return sendJson(res, 200, { ok: true, fileName: path.basename(s.source), base64: fs.readFileSync(s.source).toString('base64') });
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
