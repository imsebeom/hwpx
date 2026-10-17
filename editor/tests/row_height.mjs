// row_height 도구 회귀 시험. 지정 높이(mm)로 그려지는지, 글보다 작게 주면 실제 높이를 알리는지, 없는 행은 거부하는지.
//   node editor/tests/row_height.mjs
// 기대값은 같은 결과물을 한/글 2024 PDF 로 렌더해 표 가로선 간격으로 잰 값과 같다(2026-10-17: 4.5, 20, 12, 12mm).
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const dir = path.join(HERE, '..', 'studio-dist', 'node');
const m = await import(pathToFileURL(path.join(dir, 'rhwp.js')).href);
m.initSync({ module: fs.readFileSync(path.join(dir, 'rhwp_bg.wasm')) });
const { runTool } = await import(pathToFileURL(path.join(HERE, '..', 'plugin', 'lib', 'doc-tools.js')).href);
const doc = new m.HwpDocument(fs.readFileSync(path.join(HERE, '..', '..', 'tests', 'fixtures', 'short_table_md2hwpx.hwpx')));

const cases = [
  [{ table: 'T1', row: 1, height_mm: 20 }, (r) => r.ok && r.rows[0].drawn_mm === 20 && !r.note],
  [{ table: 'T1', row: 2, to_row: 3, height_mm: 12 }, (r) => r.ok && r.rows.every((x) => x.drawn_mm === 12)],
  [{ table: 'T1', row: 0, height_mm: 1 }, (r) => r.ok && r.rows[0].drawn_mm > 1 && /최솟값/.test(r.note)],
  [{ table: 'T1', row: 9, height_mm: 10 }, (r) => !r.ok],
  [{ table: 'T1', row: 1, height_mm: 0 }, (r) => !r.ok],
];
let failed = 0;
for (const [a, ok] of cases) {
  const r = runTool(doc, 'row_height', a).result;
  const pass = ok(r);
  failed += !pass;
  console.log(`${pass ? 'PASS' : 'FAIL'} ${JSON.stringify(a)} → ${JSON.stringify(r)}`);
}
// 내보낸 파일의 칸 높이: r1 = 20mm = 5669 HWPUNIT
const sec = (await import(pathToFileURL(path.join(HERE, '..', 'hwpx-zip.mjs')).href))
  .readZip(Buffer.from(doc.exportHwpx()), (n) => n === 'Contents/section0.xml')[0].data.toString('utf8');
const saved = sec.includes('height="5669"');
failed += !saved;
console.log(`${saved ? 'PASS' : 'FAIL'} 내보낸 XML 에 20mm(5669) 칸 높이`);
if (failed) process.exit(1);
console.log('모두 통과');
