// table_props 의 none 안전장치 회귀 시험. 한 쪽보다 긴 표는 none 을 거부하고, 짧은 표는 받아야 한다.
//   node editor/tests/table_props_guard.mjs
// 고정 파일은 스킬 tests/fixtures 의 것을 쓴다(한글 2024 로 저장한 41행 표, md2hwpx 로 만든 4행 표).
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const dir = path.join(HERE, '..', 'studio-dist', 'node');
const m = await import(pathToFileURL(path.join(dir, 'rhwp.js')).href);
m.initSync({ module: fs.readFileSync(path.join(dir, 'rhwp_bg.wasm')) });
const { runTool } = await import(pathToFileURL(path.join(HERE, '..', 'plugin', 'lib', 'doc-tools.js')).href);
const FIX = path.join(HERE, '..', '..', 'tests', 'fixtures');

const cases = [
  ['long_table_hancom_saved.hwpx', 'none', false],
  ['long_table_hancom_saved.hwpx', 'cell', true],
  ['short_table_md2hwpx.hwpx', 'none', true],
];
let failed = 0;
for (const [file, pb, wantOk] of cases) {
  const doc = new m.HwpDocument(fs.readFileSync(path.join(FIX, file)));
  // runTool 은 예외를 잡아 { result: { ok: false, error } } 로 돌려주고 문서를 되돌린다
  const { result } = runTool(doc, 'table_props', { table: 'T1', page_break: pb });
  const ok = result.ok;
  const msg = result.error || '';
  const pass = ok === wantOk;
  failed += !pass;
  console.log(`${pass ? 'PASS' : 'FAIL'} ${file} page_break=${pb}: ${ok ? '적용' : '거부'} (기대 ${wantOk ? '적용' : '거부'})${msg ? ` — ${msg}` : ''}`);
}
if (failed) process.exit(1);
console.log('모두 통과');
