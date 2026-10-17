// 표와 쪽 도구 회귀 시험: cell_style, column_width, page_setup, table_props(auto).
//   node editor/tests/table_page_tools.mjs [--out <폴더>]   (--out 이면 결과 문서를 남겨 한/글로 대조할 수 있다)
// 한/글 2024 대조(2026-10-17): 같은 결과물을 한/글 PDF 로 렌더해 선 위치, 색, 쪽 크기를 쟀다(findings 는 커밋 메시지).
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const dir = path.join(HERE, '..', 'studio-dist', 'node');
const m = await import(pathToFileURL(path.join(dir, 'rhwp.js')).href);
m.initSync({ module: fs.readFileSync(path.join(dir, 'rhwp_bg.wasm')) });
const { runTool, listTables } = await import(pathToFileURL(path.join(HERE, '..', 'plugin', 'lib', 'doc-tools.js')).href);
const { readZip } = await import(pathToFileURL(path.join(HERE, '..', 'hwpx-zip.mjs')).href);
const FIX = path.join(HERE, '..', '..', 'tests', 'fixtures');
const outDir = process.argv.includes('--out') ? process.argv[process.argv.indexOf('--out') + 1] : null;
const open = (f) => new m.HwpDocument(fs.readFileSync(path.join(FIX, f)));
const xml = (doc, name) => readZip(Buffer.from(doc.exportHwpx()), (n) => n === name)[0].data.toString('utf8');
let failed = 0;
const check = (label, ok, info = '') => { failed += !ok; console.log(`${ok ? 'PASS' : 'FAIL'} ${label}${info ? ` — ${info}` : ''}`); };

// cell_style
{
  const doc = open('short_table_md2hwpx.hwpx');
  let r = runTool(doc, 'cell_style', { table: 'T1', from_row: 1, from_col: 0, to_row: 2, to_col: 1, bg_color: '#ffff00', border: { sides: 'outer', type: 'dash', width_mm: 0.4, color: '#ff0000' }, padding_mm: 2 }).result;
  check('cell_style 범위 적용', r.ok && r.cells === 4, JSON.stringify(r));
  const h = xml(doc, 'Contents/header.xml');
  check('배경 #FFFF00 저장', /faceColor="#FFFF00"/.test(h));
  check('바깥 테두리 DASH 0.4 mm 빨강 저장', /type="DASH" width="0.4 mm" color="#FF0000"/.test(h));
  const p = J(doc.getCellProperties(...(() => { const t = listTables(doc)[0]; return [t.section, t.para, t.ctrl]; })(), 2));
  check('안쪽 여백 2mm(567)', p.paddingLeft === 567 && p.paddingTop === 567, `${p.paddingLeft}/${p.paddingTop}`);
  r = runTool(doc, 'cell_style', { table: 'T1', from_row: 0, from_col: 0, bg_color: 'red' }).result;
  check('잘못된 색은 거부', !r.ok);
  r = runTool(doc, 'cell_style', { table: 'T1', from_row: 0, from_col: 0, border: { sides: 'diag' } }).result;
  check('잘못된 sides 는 거부', !r.ok);
  if (outDir) fs.writeFileSync(path.join(outDir, 'cell_style.hwpx'), Buffer.from(doc.exportHwpx()));
}

// column_width
{
  const doc = open('short_table_md2hwpx.hwpx');
  let r = runTool(doc, 'column_width', { table: 'T1', col: 0, width_mm: 50 }).result;
  check('열 너비 50mm, 표 폭 유지', r.ok && r.columns_mm[0] === 50 && Math.abs(r.columns_mm[0] + r.columns_mm[1] - 150) < 0.2, JSON.stringify(r));
  r = runTool(doc, 'column_width', { table: 'T1', col: 0, width_mm: 160 }).result;
  check('이웃 열이 3mm 보다 좁아지면 거부', !r.ok, r.error);
  if (outDir) fs.writeFileSync(path.join(outDir, 'column_width.hwpx'), Buffer.from(doc.exportHwpx()));
}

// page_setup
{
  const doc = open('short_table_md2hwpx.hwpx');
  const r = runTool(doc, 'page_setup', { orientation: 'landscape', margins_mm: { left: 15, right: 15 } }).result;
  check('가로, 좌우 여백 15mm', r.ok && r.landscape === true && r.margins_mm.left === 15 && r.margins_mm.right === 15, JSON.stringify(r));
  // HWPX 는 세로가 WIDELY, 가로가 NARROWLY 다(한/글 2024 저장본 실측)
  check('저장 XML 에 가로 방향(NARROWLY)', /landscape="NARROWLY"/.test(xml(doc, 'Contents/section0.xml')));
  check('바꿀 것 없으면 거부', !runTool(doc, 'page_setup', {}).result.ok);
  if (outDir) fs.writeFileSync(path.join(outDir, 'page_setup.hwpx'), Buffer.from(doc.exportHwpx()));
}

// table_props auto
{
  const long = open('long_table_hancom_saved.hwpx');
  runTool(long, 'table_props', { table: 'T1', page_break: 'auto' });
  let x = xml(long, 'Contents/section0.xml');
  check('auto: 긴 표는 TABLE + 제목 줄 반복', /<hp:tbl\b[^>]*pageBreak="TABLE"[^>]*repeatHeader="1"/.test(x));
  const short = open('short_table_md2hwpx.hwpx');
  runTool(short, 'table_props', { table: 'T1', page_break: 'auto' });
  x = xml(short, 'Contents/section0.xml');
  check('auto: 짧은 표는 NONE', /<hp:tbl\b[^>]*pageBreak="NONE"/.test(x));
}

function J(s) { return typeof s === 'string' ? JSON.parse(s) : s; }
if (failed) process.exit(1);
console.log('모두 통과');
