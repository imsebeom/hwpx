/**
 * 설치된 글꼴 파일에서 글자 전진 폭(hmtx)을 읽어 엔진에 넘길 폭 표를 만든다(의존성 없음).
 *
 * 한/글은 설치된 글꼴 파일의 폭으로 줄을 나눈다. 엔진(rhwp)은 브라우저 안에서 돌아 글꼴 파일을 읽지 못하고 빌드에 넣은
 * 폭 표만 쓰므로, 표가 없는 글꼴은 한글 1.0em, 그 밖 0.5em 으로 어림해 줄 나눔이 어긋났다(2026-10-06 한컴산뜻돋움).
 * 이 PC 에서 도는 서버는 글꼴 파일을 읽을 수 있다 — 문서가 쓰는 글꼴 가운데 엔진에 표가 없는 것만 여기서 읽어
 * 엔진 패치 `registerFontMetrics`(patches/font-metrics-runtime*.rs)로 넘긴다. 서버 전처리(rhwp_layout.mjs)와
 * 브라우저 엔진이 같은 표를 받는다.
 *
 *   node font-metrics.mjs <문서.hwpx>      문서의 글꼴마다: 엔진 내장 / 파일에서 읽음(파일, 한글 폭) / 못 찾음
 *
 * 글꼴 찾기: 글꼴 폴더(Windows 는 시스템, 사용자, 한/글이 자기 폴더에 두고 쓰는 글꼴)를 훑어 이름표(name)의 가족 이름과
 * 전체 이름을 색인한다. 문서의 글꼴 이름과 같은 가족의 보통 얼굴, 굵은 얼굴을 등록한다. 전체 이름으로만 맞으면
 * (「나눔스퀘어 Bold」처럼 굵기마다 이름이 따로인 글꼴) 그 얼굴 하나를 보통으로 등록한다.
 * 색인은 `~/.claude/cache/hwpx-editor/font-index.json` 에 두고 바뀐 파일만 다시 읽는다. .hft(한/글 옛 글꼴)는 읽지 않는다.
 */
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { readZip } from './hwpx-zip.mjs';

const CACHE = path.join(os.homedir(), '.claude', 'cache', 'hwpx-editor', 'font-index.json');
const CACHE_VERSION = 1;
// 폭을 싣는 구간(엔진 내장 표와 같은 범위). 한글 음절과 한자는 따로 싣는다
const BLOCKS = [
  [0x0020, 0x007e], // ASCII
  [0x00a0, 0x00ff], // 라틴-1(가운뎃점 등)
  [0x2000, 0x206f], // 일반 문장 부호
  [0x2100, 0x27bf], // 글자꼴 기호, 로마 숫자, 화살표, 수학, 원 숫자, 괘선, 도형, 딩뱃
  [0x3000, 0x303f], // CJK 문장 부호
  [0x3130, 0x318f], // 한글 호환 자모
  [0x3200, 0x33ff], // 원 한글, 단위 기호
  [0xff00, 0xffef], // 전각, 반각 꼴
];

function fontDirs() {
  const home = os.homedir();
  if (process.platform === 'win32') {
    const local = process.env.LOCALAPPDATA || path.join(home, 'AppData', 'Local');
    const programs = [process.env['ProgramFiles(x86)'], process.env.ProgramFiles].filter(Boolean);
    return [
      path.join(process.env.WINDIR || 'C:\\Windows', 'Fonts'),
      path.join(local, 'Microsoft', 'Windows', 'Fonts'),
      ...programs.map((p) => path.join(p, 'HNC')), // 한/글은 설치하지 않은 글꼴을 자기 폴더(Shared\TTF)에 두고 쓴다
    ];
  }
  if (process.platform === 'darwin') return ['/System/Library/Fonts', '/Library/Fonts', path.join(home, 'Library', 'Fonts')];
  return ['/usr/share/fonts', '/usr/local/share/fonts', path.join(home, '.fonts'), path.join(home, '.local', 'share', 'fonts')];
}

function fontFiles() {
  const files = [];
  const walk = (dir, depth) => {
    let entries;
    try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
    for (const e of entries) {
      const p = path.join(dir, e.name);
      if (e.isDirectory()) { if (depth < 8) walk(p, depth + 1); } else if (/\.(ttf|otf|ttc)$/i.test(e.name)) files.push(p);
    }
  };
  for (const dir of fontDirs()) walk(dir, 0);
  return files;
}

function readAt(fd, pos, len) {
  const b = Buffer.alloc(len);
  return b.subarray(0, fs.readSync(fd, b, 0, len, pos));
}

/** 파일 안 글꼴들의 시작 위치(.ttc 는 여러 개) */
function faceOffsets(fd) {
  const head = readAt(fd, 0, 12);
  if (head.length < 12) return [];
  if (head.toString('latin1', 0, 4) !== 'ttcf') return [0];
  const offs = readAt(fd, 12, head.readUInt32BE(8) * 4);
  return Array.from({ length: Math.floor(offs.length / 4) }, (_, i) => offs.readUInt32BE(i * 4));
}

/** 글꼴 하나의 표 목록 { 이름: { offset, length } } */
function tableDir(fd, offset) {
  const head = readAt(fd, offset, 12);
  // TrueType(0x00010000, 'true'), CFF('OTTO')
  if (head.length < 12 || ![0x00010000, 0x74727565, 0x4f54544f].includes(head.readUInt32BE(0))) return null;
  const dir = readAt(fd, offset + 12, head.readUInt16BE(4) * 16);
  const tables = {};
  for (let i = 0; i + 16 <= dir.length; i += 16) {
    tables[dir.toString('latin1', i, i + 4)] = { offset: dir.readUInt32BE(i + 8), length: dir.readUInt32BE(i + 12) };
  }
  return tables;
}

function utf16be(raw) {
  const b = Buffer.from(raw.subarray(0, raw.length & ~1));
  b.swap16();
  return b.toString('utf16le');
}

/** 이름표: 가족 이름(1, 16)과 전체 이름(4), 모든 언어 */
function readNames(fd, table) {
  const b = readAt(fd, table.offset, Math.min(table.length, 1 << 20));
  const family = new Set();
  const full = new Set();
  if (b.length < 6) return { family: [], full: [] };
  const strings = b.readUInt16BE(4);
  for (let i = 0, r = 6; i < b.readUInt16BE(2) && r + 12 <= b.length; i++, r += 12) {
    const nameId = b.readUInt16BE(r + 6);
    if (nameId !== 1 && nameId !== 4 && nameId !== 16) continue;
    const platform = b.readUInt16BE(r);
    const start = strings + b.readUInt16BE(r + 10);
    const raw = b.subarray(start, start + b.readUInt16BE(r + 8));
    let s = '';
    if (platform === 3 || platform === 0) s = utf16be(raw);
    else if (platform === 1 && b.readUInt16BE(r + 2) === 0) s = raw.toString('latin1');
    else if (platform === 1 && b.readUInt16BE(r + 2) === 3) { try { s = new TextDecoder('euc-kr').decode(raw); } catch { /* 풀지 못하는 이름은 건너뛴다 */ } }
    s = s.replace(/\0/g, '').trim().toLowerCase();
    if (s) (nameId === 4 ? full : family).add(s);
  }
  return { family: [...family], full: [...full] };
}

/** 파일의 글꼴마다 { index, family, full, bold, italic } */
function scanFile(file) {
  const faces = [];
  let fd;
  try {
    fd = fs.openSync(file, 'r');
    faceOffsets(fd).forEach((offset, index) => {
      const t = tableDir(fd, offset);
      if (!t?.name || !t.cmap || !t.hmtx || !t.hhea || !t.head) return;
      // 굵게, 기울임: OS/2 fsSelection(5번, 0번 비트), 없으면 head macStyle
      const os2 = t['OS/2'] && t['OS/2'].length >= 64 ? readAt(fd, t['OS/2'].offset + 62, 2) : null;
      const mac = readAt(fd, t.head.offset + 44, 2);
      const bold = os2?.length === 2 ? (os2.readUInt16BE(0) & 0x20) !== 0 : mac.length === 2 && (mac.readUInt16BE(0) & 1) !== 0;
      const italic = os2?.length === 2 ? (os2.readUInt16BE(0) & 1) !== 0 : mac.length === 2 && (mac.readUInt16BE(0) & 2) !== 0;
      faces.push({ index, ...readNames(fd, t.name), bold, italic });
    });
  } catch { /* 읽지 못하는 파일은 색인에 넣지 않는다 */ } finally {
    if (fd !== undefined) fs.closeSync(fd);
  }
  return faces;
}

let indexMemo = null;
/** 이 PC 글꼴 색인: [{ file, index, family, full, bold, italic }]. 디스크 캐시에서 바뀐 파일만 다시 읽는다 */
function fontIndex() {
  if (indexMemo) return indexMemo;
  let cache = {};
  try {
    const saved = JSON.parse(fs.readFileSync(CACHE, 'utf8'));
    if (saved.version === CACHE_VERSION) cache = saved.files;
  } catch { /* 캐시 없음 */ }
  const files = {};
  let changed = false;
  for (const file of fontFiles()) {
    let st;
    try { st = fs.statSync(file); } catch { continue; }
    const old = cache[file];
    if (old && old.size === st.size && old.mtime === st.mtimeMs) files[file] = old;
    else { files[file] = { size: st.size, mtime: st.mtimeMs, faces: scanFile(file) }; changed = true; }
  }
  if (changed || Object.keys(files).length !== Object.keys(cache).length) {
    try {
      fs.mkdirSync(path.dirname(CACHE), { recursive: true });
      fs.writeFileSync(CACHE, JSON.stringify({ version: CACHE_VERSION, files }));
    } catch { /* 캐시를 못 써도 색인은 쓴다 */ }
  }
  indexMemo = Object.entries(files).flatMap(([file, f]) => f.faces.map((face) => ({ file, ...face })));
  return indexMemo;
}

/** 글자 코드 → 글리프 번호 함수. 4바이트 표(format 12)를 먼저, 없으면 2바이트 표(format 4) */
function readCmap(b) {
  let best = null;
  for (let i = 0, r = 4; i < b.readUInt16BE(2) && r + 8 <= b.length; i++, r += 8) {
    const platform = b.readUInt16BE(r);
    const encoding = b.readUInt16BE(r + 2);
    const offset = b.readUInt32BE(r + 4);
    if (offset + 4 > b.length) continue;
    const format = b.readUInt16BE(offset);
    const unicode = platform === 0 || (platform === 3 && (encoding === 1 || encoding === 10));
    if (!unicode || (format !== 4 && format !== 12)) continue;
    if (!best || format > best.format) best = { format, offset };
  }
  if (!best) return () => 0;
  const o = best.offset;
  if (best.format === 12) {
    const groups = b.readUInt32BE(o + 12);
    return (code) => {
      let lo = 0;
      let hi = groups - 1;
      while (lo <= hi) {
        const mid = (lo + hi) >> 1;
        const g = o + 16 + mid * 12;
        if (g + 12 > b.length) return 0;
        if (code < b.readUInt32BE(g)) hi = mid - 1;
        else if (code > b.readUInt32BE(g + 4)) lo = mid + 1;
        else return b.readUInt32BE(g + 8) + (code - b.readUInt32BE(g));
      }
      return 0;
    };
  }
  const segX2 = b.readUInt16BE(o + 6);
  const ends = o + 14;
  const starts = ends + segX2 + 2;
  const deltas = starts + segX2;
  const ranges = deltas + segX2;
  return (code) => {
    if (code > 0xffff) return 0;
    let lo = 0;
    let hi = segX2 / 2 - 1;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (b.readUInt16BE(ends + mid * 2) < code) lo = mid + 1; else hi = mid;
    }
    const start = b.readUInt16BE(starts + lo * 2);
    if (start > code || b.readUInt16BE(ends + lo * 2) < code) return 0;
    const delta = b.readUInt16BE(deltas + lo * 2);
    const rangeOffset = b.readUInt16BE(ranges + lo * 2);
    if (rangeOffset === 0) return (code + delta) & 0xffff;
    const at = ranges + lo * 2 + rangeOffset + (code - start) * 2;
    if (at + 2 > b.length) return 0;
    const glyph = b.readUInt16BE(at);
    return glyph ? (glyph + delta) & 0xffff : 0;
  };
}

/** 얼굴 하나의 폭 표 { em, hangul, ranges, uniform } (엔진 registerFontMetrics 형식) */
function readWidths(face) {
  const fd = fs.openSync(face.file, 'r');
  try {
    const t = tableDir(fd, faceOffsets(fd)[face.index]);
    const em = readAt(fd, t.head.offset + 18, 2).readUInt16BE(0);
    const metrics = readAt(fd, t.hhea.offset + 34, 2).readUInt16BE(0);   // 전진 폭이 따로 적힌 글리프 수
    const hmtx = readAt(fd, t.hmtx.offset, t.hmtx.length);
    const glyphOf = readCmap(readAt(fd, t.cmap.offset, t.cmap.length));
    const width = (code) => {
      const glyph = glyphOf(code);
      const at = Math.min(glyph, metrics - 1) * 4;
      if (!glyph || at + 2 > hmtx.length) return 0;
      const w = hmtx.readUInt16BE(at);
      return w > 2 * em ? 0 : w;   // em 의 두 배를 넘는 폭은 깨진 값으로 보고 없는 것으로 친다
    };
    const ranges = [];
    for (const [start, end] of BLOCKS) {
      const widths = [];
      for (let code = start; code <= end; code++) widths.push(width(code));
      while (widths.length && widths[widths.length - 1] === 0) widths.pop();
      if (widths.some((w) => w > 0)) ranges.push([start, widths]);
    }
    const syllables = [];
    for (let code = 0xac00; code <= 0xd7a3; code++) syllables.push(width(code));
    const hangul = syllables.every((w) => w > 0 && w === syllables[0]) ? syllables[0] : syllables.some((w) => w > 0) ? syllables : null;
    const hanja = new Set();
    for (let code = 0x4e00; code <= 0x9fff; code++) { const w = width(code); if (w) hanja.add(w); }
    return { em, hangul, ranges, uniform: hanja.size === 1 ? [[0x4e00, 0x9fff, [...hanja][0]]] : [] };
  } finally {
    fs.closeSync(fd);
  }
}

const metricsMemo = new Map();
/** 글꼴 이름 하나의 폭 표(보통, 있으면 굵은 얼굴). 이 PC 에 없으면 빈 배열 */
export function metricsFor(name) {
  if (metricsMemo.has(name)) return metricsMemo.get(name);
  const key = name.trim().toLowerCase();
  const index = fontIndex();
  const family = index.filter((f) => f.family.includes(key));
  const regular = family.find((f) => !f.bold && !f.italic) ?? index.find((f) => f.full.includes(key)) ?? family.find((f) => !f.italic) ?? family[0];
  const bold = regular && family.includes(regular) ? family.find((f) => f.bold && !f.italic && f !== regular) : null;
  const out = [];
  for (const [face, isBold] of [[regular, false], [bold, true]]) {
    if (!face) continue;
    try { out.push({ name, bold: isBold, file: face.file, ...readWidths(face) }); } catch { /* 깨진 글꼴 파일 */ }
  }
  metricsMemo.set(name, out);
  return out;
}

/**
 * 문서(hwpx)의 글자 모양이 가리키는 글꼴 이름. 글꼴 목록에는 쓰이지 않는 옛 글꼴이 수십 개 남아 있기도 해서
 * 목록 전체가 아니라 글자 모양(charPr fontRef)이 실제로 가리키는 것만 본다. 글자 모양을 못 읽으면 목록 전체.
 */
export function docFontFaces(hwpxBuf) {
  const header = (readZip(hwpxBuf, (n) => n === 'Contents/header.xml') || [])[0];
  if (!header) return [];
  const xml = header.data.toString('utf8');
  const byLang = {};   // 언어 → { 글꼴 번호: 이름 }
  const all = new Set();
  for (const block of xml.matchAll(/<hh:fontface\b[^>]*\blang="(\w+)"[^>]*>([\s\S]*?)<\/hh:fontface>/g)) {
    const faces = (byLang[block[1].toLowerCase()] = {});
    for (const font of block[2].matchAll(/<hh:font\b[^>]*>/g)) {
      const id = /\bid="(\d+)"/.exec(font[0])?.[1];
      const face = /\bface="([^"]*)"/.exec(font[0])?.[1];
      if (id !== undefined && face) { faces[id] = face; all.add(face); }
    }
  }
  const used = new Set();
  for (const ref of xml.matchAll(/<hh:fontRef\b([^>]*)\/>/g)) {
    for (const [, lang, id] of ref[1].matchAll(/(\w+)="(\d+)"/g)) {
      const face = byLang[lang.toLowerCase()]?.[id];
      if (face) used.add(face);
    }
  }
  return [...(used.size ? used : all)];
}

/**
 * 문서가 쓰는 글꼴 가운데 엔진에 폭 표가 없는 것을 글꼴 파일에서 읽는다.
 * mod = 엔진 모듈(rhwp.js). 반환 { metrics: 등록할 폭 표, read: 읽은 글꼴 이름, missing: 이 PC 에 없는 글꼴 이름 }.
 * 패치가 없는 엔진(npm 원본)이면 아무것도 하지 않는다.
 */
export function docFontMetrics(hwpxBuf, mod) {
  const result = { metrics: [], read: [], missing: [] };
  if (typeof mod?.hasBuiltinFontMetric !== 'function') return result;
  for (const name of docFontFaces(hwpxBuf)) {
    if (mod.hasBuiltinFontMetric(name)) continue;
    const faces = metricsFor(name);
    if (!faces.length) { result.missing.push(name); continue; }
    result.read.push(name);
    result.metrics.push(...faces.map(({ file, ...metric }) => metric));
  }
  return result;
}

/** 폭 표를 엔진 모듈에 등록한다(이미 등록한 것은 엔진이 건너뛴다). 반환: 새로 등록한 얼굴 수 */
export function registerInto(mod, metrics) {
  if (!metrics.length || typeof mod?.registerFontMetrics !== 'function') return 0;
  return mod.registerFontMetrics(JSON.stringify(metrics));
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const file = process.argv[2];
  if (!file) { console.error('사용법: node font-metrics.mjs <문서.hwpx>'); process.exit(2); }
  const dir = process.env.RHWP_ENGINE || path.join(path.dirname(fileURLToPath(import.meta.url)), 'studio-dist', 'node');
  const mod = await import(pathToFileURL(path.join(dir, 'rhwp.js')).href);
  mod.initSync({ module: fs.readFileSync(path.join(dir, 'rhwp_bg.wasm')) });
  const buf = fs.readFileSync(file);
  for (const name of docFontFaces(buf)) {
    if (mod.hasBuiltinFontMetric?.(name)) { console.log(`내장      ${name}`); continue; }
    const faces = metricsFor(name);
    if (!faces.length) { console.log(`못 찾음   ${name}`); continue; }
    for (const f of faces) {
      const hangul = Array.isArray(f.hangul) ? '음절마다 다름' : f.hangul ?? '없음';
      console.log(`파일      ${name}${f.bold ? ' (굵게)' : ''} ← ${path.basename(f.file)}  em ${f.em}, 한글 ${hangul}, 구간 ${f.ranges.length}, 한자 ${f.uniform[0]?.[2] ?? '없음'}`);
    }
  }
  const r = docFontMetrics(buf, mod);
  console.log(`등록 ${registerInto(mod, r.metrics)}개 얼굴 (읽음 ${r.read.length}, 못 찾음 ${r.missing.length})`);
}
