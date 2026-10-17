// 본문 문단의 선택 사각형을 찍는다: node selrects.mjs <wasm폴더> <hwpx> <문단> [시작 글자=0] [끝 글자=문단 끝]
// 여러 줄 문단을 처음부터 끝까지 고르면 줄마다 사각형 하나가 나와야 한다. 줄 시작(getLineStarts)과 함께 찍는다.
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const [dir, file, paraArg, fromArg, toArg] = process.argv.slice(2);
const m = await import(pathToFileURL(path.join(dir, 'rhwp.js')).href);
m.initSync({ module: fs.readFileSync(path.join(dir, 'rhwp_bg.wasm')) });
const { docFontMetrics, registerInto } = await import(pathToFileURL('C:/Users/hccga/.claude/skills/hwpx/editor/font-metrics.mjs').href);
const bytes = fs.readFileSync(file);
registerInto(m, docFontMetrics(bytes, m).metrics);
const doc = new m.HwpDocument(bytes);
const para = Number(paraArg);
const starts = doc.getLineStarts ? JSON.parse(doc.getLineStarts(0, para)) : null;
const len = doc.getParagraphLength ? doc.getParagraphLength(0, para) : Number(toArg ?? 0);
const from = Number(fromArg ?? 0);
const to = toArg !== undefined ? Number(toArg) : len;
console.log('줄 시작', JSON.stringify(starts), '문단 길이', len, '선택', from, '→', to);
const rects = JSON.parse(doc.getSelectionRects(0, para, from, para, to));
for (const r of rects) console.log(`  쪽 ${r.pageIndex} x ${r.x.toFixed(1)} y ${r.y.toFixed(1)} 폭 ${r.width.toFixed(1)} 높이 ${r.height.toFixed(1)}`);
for (const off of [from, to]) {
  const c = JSON.parse(doc.getCursorRect(0, para, off));
  console.log(`  커서 ${off}: x ${c.x.toFixed(1)} y ${c.y.toFixed(1)}`);
}
