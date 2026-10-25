// 편집 순서 시험: 편집 도구를 2~3개 이어서 적용하며 단계마다 엔진이 가진 조판을, 같은 결과 문서를 줄 배치 캐시 없이
// 처음부터 다시 조판한 것과 맞댄다. edit_consistency.mjs 는 도구마다 원본에서 새로 시작해 앞 편집이 남긴 상태가 다음 편집에서
// 드러나는 결함을 못 잡는다(2026-10-25 「긴 글 → 글자처럼 취급 끄기 → 짧은 글」 에서 칸 높이가 줄지 않았다).
//   node editor/tests/edit_sequence.mjs <문서> [--mode pairs|triples|all] [--batch] [--only 이름,이름] [--out 결과.json]
//   --batch: 한 순서를 에디터의 run 한 번처럼 한 지연 조판 묶음으로 적용한다(기본은 단계마다 묶음 하나)
// 대상(표, 칸, 문단)은 문서에서 고른다: 칸이 가장 많은 표, 그 표의 마지막 칸, 글이 30자 넘는 첫 본문 문단.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const EDITOR = path.join(HERE, '..');
const argv = process.argv.slice(2);
const opt = (k, d) => (argv.includes(k) ? argv[argv.indexOf(k) + 1] : d);
const file = argv.find((a, i) => !a.startsWith('--') && !argv[i - 1]?.startsWith('--'));
const mode = opt('--mode', 'all');
const batch = argv.includes('--batch');
const only = opt('--only', '') ? new Set(opt('--only', '').split(',')) : null;
const dir = path.join(EDITOR, 'studio-dist', 'node');
const m = await import(pathToFileURL(path.join(dir, 'rhwp.js')).href);
m.initSync({ module: fs.readFileSync(path.join(dir, 'rhwp_bg.wasm')) });
const { docFontMetrics, registerInto } = await import(pathToFileURL(path.join(EDITOR, 'font-metrics.mjs')).href);
const { readZip, writeZip } = await import(pathToFileURL(path.join(EDITOR, 'hwpx-zip.mjs')).href);
const { stepCore, paraTextAt } = await import(pathToFileURL(path.join(EDITOR, 'plugin', 'lib', 'run-ops.js')).href);
const { listTables } = await import(pathToFileURL(path.join(EDITOR, 'plugin', 'lib', 'doc-tools.js')).href);

const src = fs.readFileSync(file);
const isZip = src[0] === 0x50 && src[1] === 0x4b;
registerInto(m, docFontMetrics(src, m).metrics);

function stripped(buf) {
  const entries = readZip(buf);
  for (const e of entries) {
    if (/^Contents\/section\d+\.xml$/.test(e.name)) e.data = Buffer.from(e.data.toString('utf8').replace(/<hp:linesegarray>[\s\S]*?<\/hp:linesegarray>/g, ''), 'utf8');
  }
  return writeZip(entries);
}
const open = () => new m.HwpDocument(isZip ? stripped(src) : src);

/** 조판 지문(edit_consistency.mjs 와 같은 기준): 쪽수, 본문 문단 [줄 시작, 쪽], 칸 문단 줄 시작 */
function layout(doc) {
  const out = { pages: doc.pageCount(), body: [], cells: [] };
  for (let s = 0; s < doc.getSectionCount(); s++) {
    for (let p = 0; p < doc.getParagraphCount(s); p++) {
      let page = -1;
      try { page = JSON.parse(doc.getPageOfPosition(s, p)).page; } catch { /* 쪽 없음 */ }
      out.body.push({ p, page, starts: s === 0 ? doc.getLineStarts(0, p) : '' });
    }
  }
  try {
    for (const l of (JSON.parse(doc.getCursorModel()).lists || []).filter((x) => x.isCell)) {
      for (let p = 0; p < (l.paraCount || 0); p++) out.cells.push(`${l.listId}:${p}=${doc.getLineStarts(l.listId, p)}`);
    }
  } catch { /* 칸 목록 없음 */ }
  return out;
}
function diff(a, b) {
  const d = [];
  if (a.pages !== b.pages) d.push(`쪽수 ${a.pages}≠새로 ${b.pages}`);
  for (let i = 0; i < Math.max(a.body.length, b.body.length) && d.length < 3; i++) {
    const x = a.body[i];
    const y = b.body[i];
    if (!x || !y) { d.push(`문단 수 ${a.body.length}≠${b.body.length}`); break; }
    if (x.starts !== y.starts) d.push(`p${x.p} 줄 ${x.starts}≠${y.starts}`);
    else if (x.page !== y.page) d.push(`p${x.p} 쪽 ${x.page + 1}≠${y.page + 1}`);
  }
  if (a.cells.length !== b.cells.length) d.push(`칸 문단 수 ${a.cells.length}≠${b.cells.length}`);
  else {
    const bad = a.cells.filter((c, i) => c !== b.cells[i]);
    if (bad.length) d.push(`칸 문단 ${bad.length}곳 줄 다름(${bad[0]} 대 ${b.cells[a.cells.indexOf(bad[0])]})`);
  }
  return d;
}
// 문서 객체는 WASM 메모리를 쓰므로 다 쓰면 free 한다(안 하면 순서 1,000개쯤에서 4GB 한도에 닿는다)
function check(doc) {
  const fresh = new m.HwpDocument(stripped(Buffer.from(doc.exportHwpx())));
  try {
    return diff(layout(doc), layout(fresh));
  } finally {
    fresh.free();
  }
}

// ── 대상 고르기 ──
const base = open();
const tables = listTables(base).map((t) => ({ ...t, ...JSON.parse(base.getTableDimensions(t.section, t.para, t.ctrl)) }));
const T = tables.filter((t) => t.section === 0).sort((a, b) => b.cellCount - a.cellCount)[0];
let P = -1;
for (let p = 0; p < base.getParagraphCount(0) && P < 0; p++) if (paraTextAt(base, 0, p).trim().length > 30) P = p;
base.free();
const LONG = '긴 글을 넣어 칸과 문단을 키웁니다. '.repeat(60);
const r = T ? T.rowCount - 1 : 0;
const c = T ? T.colCount - 1 : 0;
const tool = (name, args) => ({ tool: name, args });
const tblProps = (props) => ({ doc: 'setTableProperties', a: [T.section, T.para, T.ctrl, props] });

/** [이름, 갈래(grow|shrink|prop), op 만들기]. 대상이 없으면 그 작업은 빠진다 */
const OPS = [
  ['cellLong', 'grow', T && tool('set_cell', { table: T.id, row: r, col: c, text: LONG })],
  ['paraLong', 'grow', P >= 0 && tool('replace_paragraph', { para: P, text: LONG, keep_style: true })],
  ['insParas', 'grow', P >= 0 && tool('insert_paragraphs', { after_para: P, texts: [LONG, LONG, LONG] })],
  ['dupRow', 'grow', T && tool('duplicate_row', { table: T.id, row: r, count: 4, with_text: true })],
  ['sizeUp', 'grow', T && tool('format_text', { at: T.id, size_pt: 20 })],
  ['rowHigh', 'grow', T && tool('row_height', { table: T.id, row: r, height_mm: 80 })],
  ['spacingUp', 'grow', P >= 0 && tool('format_paragraph', { at: `p${P}`, line_spacing: 300 })],
  ['footnote', 'grow', P >= 0 && tool('add_footnote', { para: P, text: LONG.slice(0, 200) })],
  ['cellShort', 'shrink', T && tool('set_cell', { table: T.id, row: r, col: c, text: '짧은 글' })],
  ['paraShort', 'shrink', P >= 0 && tool('replace_paragraph', { para: P, text: '짧은 문단', keep_style: true })],
  ['delRow', 'shrink', T && T.rowCount > 1 && tool('delete_table_row', { table: T.id, row: r })],
  ['sizeDown', 'shrink', T && tool('format_text', { at: T.id, size_pt: 8 })],
  ['rowLow', 'shrink', T && tool('row_height', { table: T.id, row: r, height_mm: 3 })],
  ['spacingDown', 'shrink', P >= 0 && tool('format_paragraph', { at: `p${P}`, line_spacing: 100 })],
  ['tacOff', 'prop', T && tblProps({ treatAsChar: false })],
  ['tacOn', 'prop', T && tblProps({ treatAsChar: true })],
  ['pbCell', 'prop', T && tool('table_props', { table: T.id, page_break: 'cell' })],
  ['pbSplit', 'prop', T && tool('table_props', { table: T.id, page_break: 'split' })],
  ['pbNone', 'prop', T && tool('table_props', { table: T.id, page_break: 'none' })],
  ['repeatHdr', 'prop', T && tool('table_props', { table: T.id, repeat_header: true })],
  ['colWidth', 'prop', T && tool('column_width', { table: T.id, col: 0, width_mm: 15 })],
  ['padding', 'prop', T && tool('cell_style', { table: T.id, from_row: 0, from_col: 0, to_row: r, to_col: c, padding_mm: 4 })],
  ['border', 'prop', T && tool('cell_style', { table: T.id, from_row: 0, from_col: 0, to_row: r, to_col: c, border: { type: 'solid', width_mm: 1 } })],
  ['caption', 'prop', T && tool('table_caption', { table: T.id, text: '표 설명 글', position: 'bottom' })],
  ['merge', 'prop', T && T.colCount > 1 && tool('merge_cells', { table: T.id, from_row: r, from_col: 0, to_row: r, to_col: 1 })],
  ['insCol', 'prop', T && tool('insert_table_column', { table: T.id, col: c, right: true })],
  ['delCol', 'prop', T && T.colCount > 1 && tool('delete_table_column', { table: T.id, col: c })],
  ['insRow', 'prop', T && tool('insert_table_row', { table: T.id, row: r, below: true })],
  ['margins', 'prop', tool('page_setup', { margins_mm: { top: 40, bottom: 40, left: 40, right: 40 } })],
  ['landscape', 'prop', tool('page_setup', { orientation: 'landscape' })],
  ['keepNext', 'prop', P >= 0 && tool('format_paragraph', { at: `p${P}`, keep_with_next: true })],
  ['breakBefore', 'prop', P >= 0 && tool('format_paragraph', { at: `p${P}`, page_break_before: true })],
  ['alignCenter', 'prop', P >= 0 && tool('format_paragraph', { at: `p${P}`, align: 'center' })],
  ['indent', 'prop', P >= 0 && tool('format_paragraph', { at: `p${P}`, left_margin_pt: 60 })],
  ['bullet', 'prop', P >= 0 && tool('set_list', { at: `p${P}`, kind: 'bullet' })],
  ['header', 'prop', tool('set_header_footer', { which: 'header', text: '머리말 글', align: 'center' })],
  ['bold', 'prop', P >= 0 && tool('format_text', { at: `p${P}`, bold: true })],
].filter(([, , op]) => op);

const byName = new Map(OPS.map(([n, k, op]) => [n, { k, op }]));
const GROW_SHRINK = [['cellLong', 'cellShort'], ['paraLong', 'paraShort'], ['sizeUp', 'sizeDown'], ['rowHigh', 'rowLow'], ['spacingUp', 'spacingDown'], ['dupRow', 'delRow'], ['insParas', 'paraShort']]
  .filter(([g, s]) => byName.has(g) && byName.has(s));

const seqs = [];
if (mode !== 'triples') for (const [a] of OPS) for (const [b] of OPS) seqs.push([a, b]);
if (mode !== 'pairs') {
  for (const [g, s] of GROW_SHRINK) {
    for (const [p, k] of OPS) if (k === 'prop') { seqs.push([g, p, s]); seqs.push([p, g, s]); }
  }
}

// ── 실행 ──
// 같은 순서 접두가 실패하면 그 뒤 순서는 다시 돌리지 않는다(단일 작업 결과는 따로 모은다)
const single = new Map();
const results = [];
const t0 = Date.now();
for (const seq of seqs) {
  if (only && !seq.some((n) => only.has(n))) continue;
  const doc = open();
  const marks = [];
  let status = 'SAME';
  try {
    if (batch) doc.beginDeferredPagination();
    for (const [i, name] of seq.entries()) {
      if (!batch) doc.beginDeferredPagination();
      try {
        stepCore(doc, byName.get(name).op);
      } finally {
        if (!batch) doc.flushDeferredPagination();
      }
      if (batch && i < seq.length - 1) continue;
      const d = check(doc);
      marks.push(d.length ? `${i + 1}단계 ${d.join(' | ')}` : `${doc.pageCount()}쪽`);
      if (d.length) { status = i === 0 ? 'FIRST' : 'DIFF'; break; }
    }
    if (batch) doc.flushDeferredPagination();
  } catch (e) {
    status = 'ERR';
    marks.push(String(e?.message ?? e).slice(0, 140));
  }
  doc.free();
  if (seq.length === 2 && status === 'FIRST') single.set(seq[0], marks.at(-1));
  results.push({ seq, status, marks });
  if (results.length % 100 === 0) process.stderr.write(`  ${results.length}/${seqs.length} ${((Date.now() - t0) / 1000).toFixed(0)}초\n`);
}

// 첫 작업만으로 어긋나는 것(단일 작업 결함)과, 앞 단계는 같았는데 뒤에서 어긋나는 것(상태가 남는 결함)을 나눠 보인다
const diffs = results.filter((x) => x.status === 'DIFF');
const errs = results.filter((x) => x.status === 'ERR');
console.log(`문서 ${path.basename(file)} — 표 ${T?.id ?? '없음'}(${T?.rowCount}×${T?.colCount}, 칸 r${r}c${c}), 문단 p${P}, 작업 ${OPS.length}개, 순서 ${results.length}개, ${((Date.now() - t0) / 1000).toFixed(0)}초`);
console.log(`\n[단일 작업만으로 어긋남] ${single.size}개`);
for (const [n, mk] of single) console.log(`  ${n} — ${mk}`);
console.log(`\n[앞 단계는 같고 뒤에서 어긋남] ${diffs.length}개`);
for (const x of diffs) console.log(`  ${x.seq.join(' → ')} — ${x.marks.join(' / ')}`);
const errOps = new Map();
for (const x of errs) errOps.set(x.marks.at(-1), (errOps.get(x.marks.at(-1)) || []).concat(x.seq.join('→')));
console.log(`\n[작업 실패(거부, 예외)] ${errs.length}개, 메시지 ${errOps.size}종`);
for (const [msg, list] of errOps) console.log(`  ${list.length}건 ${msg} (예: ${list[0]})`);
if (opt('--out')) fs.writeFileSync(opt('--out'), JSON.stringify({ file, T, P, results }, null, 1));
process.exitCode = diffs.length || single.size ? 1 : 0;
