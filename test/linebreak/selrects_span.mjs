// 본문 여러 문단에 걸친 선택 사각형: node selrects_span.mjs <wasm폴더> <hwpx> <시작 문단> <시작 글자> <끝 문단> <끝 글자|ctrl+1|ctrl>
// 끝 글자에 ctrl+1 을 주면 끝 문단 첫 조판 부호(표) 바로 뒤, ctrl 이면 바로 앞까지 고른다.
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const [dir, file, sp, so, ep, eoArg] = process.argv.slice(2);
const m = await import(pathToFileURL(path.join(dir, 'rhwp.js')).href);
m.initSync({ module: fs.readFileSync(path.join(dir, 'rhwp_bg.wasm')) });
const doc = new m.HwpDocument(fs.readFileSync(file));
const positions = JSON.parse(doc.getControlTextPositions(0, Number(ep)));
let eo = Number(eoArg);
if (eoArg === 'ctrl+1') eo = positions[0] + 1;
if (eoArg === 'ctrl') eo = positions[0];
console.log('끝 문단 조판 부호 위치', JSON.stringify(positions), '끝 글자', eo, '쪽수', doc.pageCount());
for (const r of JSON.parse(doc.getSelectionRects(0, Number(sp), Number(so), Number(ep), eo))) {
  console.log(`  쪽 ${r.pageIndex} x ${r.x.toFixed(1)} y ${r.y.toFixed(1)} 폭 ${r.width.toFixed(1)} 높이 ${r.height.toFixed(1)}`);
}
