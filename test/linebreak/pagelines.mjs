// 에디터와 같은 조건(wasm 엔진 + 글꼴 폭 표 등록)으로 문서를 조판해 쪽마다 첫 줄과 끝 줄을 찍는다.
//   node pagelines.mjs <wasm폴더> <hwpx> [쪽 번호(1부터)…]
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const [dir, file, ...want] = process.argv.slice(2);
const m = await import(pathToFileURL(path.join(dir, 'rhwp.js')).href);
m.initSync({ module: fs.readFileSync(path.join(dir, 'rhwp_bg.wasm')) });
const { docFontMetrics, registerInto } = await import(pathToFileURL('C:/Users/hccga/.claude/skills/hwpx/editor/font-metrics.mjs').href);
const bytes = fs.readFileSync(file);
registerInto(m, docFontMetrics(bytes, m).metrics);
const doc = new m.HwpDocument(bytes);
console.log('쪽수', doc.pageCount());
const pages = want.length ? want.map(Number) : [...Array(doc.pageCount()).keys()].map((i) => i + 1);
for (const pg of pages) {
  const svg = doc.renderPageSvg(pg - 1);
  const lines = new Map();
  for (const mm of svg.matchAll(/<text[^>]*?x="([\d.]+)"[^>]*?y="([\d.]+)"[^>]*>([^<]*)<\/text>/g)) {
    const y = Math.round(Number(mm[2]) * 0.75);
    if (!lines.has(y)) lines.set(y, []);
    lines.get(y).push([Number(mm[1]), mm[3].replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')]);
  }
  const ys = [...lines.keys()].sort((a, b) => a - b);
  const txt = (y) => lines.get(y).sort((a, b) => a[0] - b[0]).map((c) => c[1]).join('').slice(0, 40);
  console.log(`== ${pg}쪽 첫 3줄`, ys.slice(0, 3).map((y) => [y, txt(y)]));
  console.log('   끝 4줄', ys.slice(-4).map((y) => [y, txt(y)]));
}
