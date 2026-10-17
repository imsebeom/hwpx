// C 묶음 도구 회귀 시험: duplicate_row(서식째 행 복제), set_header_footer(쪽 번호), add_endnote, insert_equation.
//   node editor/tests/batch_c_tools.mjs [--out <폴더>]
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const dir = path.join(HERE, '..', 'studio-dist', 'node');
const m = await import(pathToFileURL(path.join(dir, 'rhwp.js')).href);
m.initSync({ module: fs.readFileSync(path.join(dir, 'rhwp_bg.wasm')) });
const { runTool } = await import(pathToFileURL(path.join(HERE, '..', 'plugin', 'lib', 'doc-tools.js')).href);
const { readZip } = await import(pathToFileURL(path.join(HERE, '..', 'hwpx-zip.mjs')).href);
const FIX = path.join(HERE, '..', '..', 'tests', 'fixtures');
const outDir = process.argv.includes('--out') ? process.argv[process.argv.indexOf('--out') + 1] : null;
const open = () => new m.HwpDocument(fs.readFileSync(path.join(FIX, 'short_table_md2hwpx.hwpx')));
const part = (doc, name) => readZip(Buffer.from(doc.exportHwpx()), (n) => n === name)[0].data.toString('utf8');
const save = (doc, name) => outDir && fs.writeFileSync(path.join(outDir, name), Buffer.from(doc.exportHwpx()));
const J = (s) => JSON.parse(s);
let failed = 0;
const check = (label, ok, info = '') => { failed += !ok; console.log(`${ok ? 'PASS' : 'FAIL'} ${label}${info ? ` — ${info}` : ''}`); };

// 첫 표의 위치(문단, 컨트롤)
const firstTable = (doc) => {
  for (let p = 0; p < doc.getParagraphCount(0); p++) {
    try { J(doc.getTableProperties(0, p, 0)); return { para: p, ctrl: 0 }; } catch { /* 표 아님 */ }
  }
  throw new Error('표가 없다');
};

// duplicate_row: 배경, 글자 모양, 글을 그대로 옮긴다
{
  const doc = open();
  const t = firstTable(doc);
  const dim0 = J(doc.getTableDimensions(0, t.para, t.ctrl));
  const cols = dim0.colCount;
  const idx = (r, c) => r * cols + c;
  doc.setCellProperties(0, t.para, t.ctrl, idx(1, 0), JSON.stringify({ fillType: 'solid', fillColor: '#ffff00' }));
  runTool(doc, 'format_text', { at: 'T1r1c1', color: '#ff0000' });
  const srcFill = J(doc.getCellProperties(0, t.para, t.ctrl, idx(1, 0)));
  const srcShape = J(doc.getCellCharPropertiesAt(0, t.para, t.ctrl, idx(1, 1), 0, 0)).charShapeId;
  const r = runTool(doc, 'duplicate_row', { table: 'T1', row: 1, count: 2 }).result;
  check('행 복제 2개', r.ok && r.rowCount === dim0.rowCount + 2, JSON.stringify(r));
  const dupFill = J(doc.getCellProperties(0, t.para, t.ctrl, idx(3, 0)));
  check('배경 옮김', dupFill.fillColor === srcFill.fillColor && dupFill.fillType === srcFill.fillType, `${dupFill.fillType} ${dupFill.fillColor}`);
  const dupShape = J(doc.getCellCharPropertiesAt(0, t.para, t.ctrl, idx(3, 1), 0, 0)).charShapeId;
  check('글자 모양 옮김', dupShape === srcShape, `${srcShape} → ${dupShape}`);
  const txt = (row, col) => {
    const n = doc.getCellParagraphLength(0, t.para, t.ctrl, idx(row, col), 0);
    return doc.getTextInCell(0, t.para, t.ctrl, idx(row, col), 0, 0, n);
  };
  check('글 옮김', txt(2, 1) === txt(1, 1) && txt(3, 1) === txt(1, 1), `${txt(1, 1)} / ${txt(3, 1)}`);
  const r2 = runTool(doc, 'duplicate_row', { table: 'T1', row: 1, with_text: false }).result;
  check('서식만 복제는 빈 칸', r2.ok && txt(2, 1) === '', JSON.stringify(txt(2, 1)));
  check('범위 밖 행 거부', !runTool(doc, 'duplicate_row', { table: 'T1', row: 99 }).result.ok);
  save(doc, 'duplicate_row.hwpx');
}

// set_header_footer: {쪽} 은 쪽 번호 필드로 저장
{
  const doc = open();
  const r = runTool(doc, 'set_header_footer', { which: 'footer', text: '- {쪽} -', align: 'center' }).result;
  check('꼬리말 쪽 번호', r.ok, JSON.stringify(r));
  const sec = part(doc, 'Contents/section0.xml');
  const foot = sec.match(/<hp:footer\b[\s\S]*?<\/hp:footer>/)?.[0] || '';
  check('쪽 번호 자동 번호로 저장', /<hp:autoNum\b[^>]*numType="PAGE"/.test(foot) && /<hp:t>- <\/hp:t>/.test(foot), foot.slice(0, 160));
  check('「쪽 번호」 낱말 거부', !runTool(doc, 'set_header_footer', { which: 'footer', text: '쪽 번호' }).result.ok);
  save(doc, 'footer_page.hwpx');
}

// add_endnote, insert_equation
{
  const doc = open();
  let r = runTool(doc, 'add_endnote', { para: 0, text: '정답: 3' }).result;
  check('미주 달기', r.ok && r.number === 1, JSON.stringify(r));
  let sec = part(doc, 'Contents/section0.xml');
  const en = sec.match(/<hp:endNote\b[\s\S]*?<\/hp:endNote>/)?.[0] || '';
  check('미주 글 저장', /정답: 3/.test(en), en.slice(0, 160));
  r = runTool(doc, 'insert_equation', { para: 0, script: '1 over 2' }).result;
  check('수식 넣기', r.ok, JSON.stringify(r));
  sec = part(doc, 'Contents/section0.xml');
  check('수식 스크립트 저장', /<hp:equation\b[\s\S]*?<hp:script>1 over 2<\/hp:script>/.test(sec));
  check('빈 수식 거부', !runTool(doc, 'insert_equation', { para: 0, script: ' ' }).result.ok);
  save(doc, 'endnote_equation.hwpx');
}

if (failed) process.exit(1);
console.log('모두 통과');
