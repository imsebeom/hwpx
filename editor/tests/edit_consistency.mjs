// 편집 뒤 조판 일관성 시험: 도구 하나를 적용한 직후 엔진이 가진 조판(쪽수, 본문 문단마다 줄 시작과 놓인 쪽, 칸 문단 줄 시작)을
// 같은 결과 문서를 줄 배치 캐시 없이 처음부터 다시 조판한 것과 맞댄다. 다르면 그 도구가 높이나 쪽 계산을 빠뜨린 것이다.
//   node editor/tests/edit_consistency.mjs <문서.hwpx> <작업.json> [--deferred]
//   --stored: 시작 문서를 저장된 줄 배치 그대로 연다(기본은 줄 배치를 지우고 연다)
//   --deferred: 에디터의 Claude 명령처럼 beginDeferredPagination … flushDeferredPagination 으로 감싼다
// 작업 JSON: [{ "label": "이름", "op": { "tool": …, "args": … } }, …] — 작업마다 원본에서 새로 시작한다.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const EDITOR = path.join(HERE, '..');
const [file, opsFile] = process.argv.slice(2).filter((a) => !a.startsWith('--'));
const deferred = process.argv.includes('--deferred');
const dir = path.join(EDITOR, 'studio-dist', 'node');
const m = await import(pathToFileURL(path.join(dir, 'rhwp.js')).href);
m.initSync({ module: fs.readFileSync(path.join(dir, 'rhwp_bg.wasm')) });
const { docFontMetrics, registerInto } = await import(pathToFileURL(path.join(EDITOR, 'font-metrics.mjs')).href);
const { readZip, writeZip } = await import(pathToFileURL(path.join(EDITOR, 'hwpx-zip.mjs')).href);
const { stepCore } = await import(pathToFileURL(path.join(EDITOR, 'plugin', 'lib', 'run-ops.js')).href);

const src = fs.readFileSync(file);
registerInto(m, docFontMetrics(src, m).metrics);
const cases = JSON.parse(fs.readFileSync(opsFile, 'utf8'));

/** 줄 배치 캐시를 모두 지운 사본(처음부터 다시 조판하게) */
function stripped(buf) {
  const entries = readZip(buf);
  for (const e of entries) {
    if (/^Contents\/section\d+\.xml$/.test(e.name)) e.data = Buffer.from(e.data.toString('utf8').replace(/<hp:linesegarray>[\s\S]*?<\/hp:linesegarray>/g, ''), 'utf8');
  }
  return writeZip(entries);
}

/** 조판 지문: 쪽수, 본문 문단마다 [줄 시작, 쪽], 칸 문단 줄 시작(커서 모형의 칸 목록 차례) */
function layout(doc) {
  const out = { pages: doc.pageCount(), body: [], cells: [] };
  const sections = doc.getSectionCount ? doc.getSectionCount() : 1;
  for (let s = 0; s < sections; s++) {
    const n = doc.getParagraphCount(s);
    for (let p = 0; p < n; p++) {
      let page = -1;
      try { page = JSON.parse(doc.getPageOfPosition(s, p)).page; } catch { /* 쪽 없음 */ }
      out.body.push({ s, p, page, starts: s === 0 ? doc.getLineStarts(0, p) : '' });
    }
  }
  try {
    const cm = JSON.parse(doc.getCursorModel());
    for (const l of (cm.lists || []).filter((x) => x.isCell)) {
      for (let p = 0; p < (l.paraCount || 0); p++) out.cells.push(`${l.listId}:${p}=${doc.getLineStarts(l.listId, p)}`);
    }
  } catch { /* 칸 목록 없음 */ }
  return out;
}

function diff(a, b) {
  const d = [];
  if (a.pages !== b.pages) d.push(`쪽수 ${a.pages} ≠ 새로 조판 ${b.pages}`);
  const n = Math.max(a.body.length, b.body.length);
  for (let i = 0; i < n && d.length < 6; i++) {
    const x = a.body[i];
    const y = b.body[i];
    if (!x || !y) { d.push(`문단 수 다름 ${a.body.length} ≠ ${b.body.length}`); break; }
    if (x.starts !== y.starts) d.push(`p${x.p} 줄 ${x.starts} ≠ ${y.starts}`);
    else if (x.page !== y.page) d.push(`p${x.p} 쪽 ${x.page + 1} ≠ ${y.page + 1}`);
  }
  if (a.cells.length !== b.cells.length) d.push(`칸 문단 수 ${a.cells.length} ≠ ${b.cells.length}`);
  else {
    const bad = a.cells.filter((c, i) => c !== b.cells[i]);
    if (bad.length) d.push(`칸 문단 ${bad.length}곳 줄 다름(예: ${bad[0]} 대 ${b.cells[a.cells.indexOf(bad[0])]})`);
  }
  return d;
}

let failed = 0;
for (const c of cases) {
  // 시작도 처음부터 조판한 상태에서 한다(저장된 줄 배치와 새 조판의 차이를 빼고 편집이 빠뜨린 계산만 본다). --stored 면 저장본 그대로
  const doc = new m.HwpDocument(process.argv.includes('--stored') ? src : stripped(src));
  let r;
  try {
    if (deferred) doc.beginDeferredPagination();
    r = stepCore(doc, c.op);
    if (deferred) doc.flushDeferredPagination();
  } catch (e) {
    console.log(`ERR  ${c.label} — ${String(e?.message ?? e).slice(0, 160)}`);
    continue;
  }
  const after = layout(doc);
  const fresh = layout(new m.HwpDocument(stripped(Buffer.from(doc.exportHwpx()))));
  const d = diff(after, fresh);
  failed += d.length > 0;
  console.log(`${d.length ? 'DIFF' : 'SAME'} ${c.label}${d.length ? ` — ${d.join(' | ')}` : ''}`);
}
console.log(failed ? `조판이 어긋난 도구 ${failed}개` : '모두 같음');
process.exitCode = failed ? 1 : 0;
