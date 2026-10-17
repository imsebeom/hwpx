// 칸 목록 하나의 문단에 대해 rhwp 의 줄 정보와 글자 x 를 찍는다.  node cellprobe.mjs <id> <칸 목록 순번> <문단>
import fs from 'node:fs';
import { pathToFileURL } from 'node:url';
const ED = 'C:/Users/hccga/.claude/skills/hwpx/editor/';
const m = await import(pathToFileURL(ED + 'studio-dist/node/rhwp.js').href);
m.initSync({ module: fs.readFileSync(ED + 'studio-dist/node/rhwp_bg.wasm') });
const { readZip, writeZip } = await import(pathToFileURL(ED + 'hwpx-zip.mjs').href);
const { docFontMetrics, registerInto } = await import(pathToFileURL(ED + 'font-metrics.mjs').href);
const [id, li, pi] = process.argv.slice(2).map((x, i) => (i ? +x : x));
const es = readZip(fs.readFileSync(`out/oracle/${id}.hwpx`));
for (const e of es) if (/^Contents\/section\d+\.xml$/.test(e.name)) e.data = Buffer.from(e.data.toString('utf8').replace(/<hp:linesegarray>[\s\S]*?<\/hp:linesegarray>/g, ''), 'utf8');
const input = writeZip(es);
registerInto(m, docFontMetrics(input, m).metrics);
const doc = new m.HwpDocument(input);
const cm = JSON.parse(doc.getCursorModel());
const l = cm.lists.filter((x) => x.isCell)[li];
console.log(JSON.stringify(l));
console.log('starts', doc.getLineStarts(l.listId, pi));
const r = (k) => JSON.parse(doc.getCursorRectInCell(0, l.hostPara, l.controlIndex, l.cellIndex, pi, k));
console.log('lineinfo0', doc.getLineInfoInCell(0, l.hostPara, l.controlIndex, l.cellIndex, pi, 0));
for (const k of [0, 1, 2, 40, 43, 44, 45, 46, 47]) { const a = r(k); console.log(k, (a.x * 0.75).toFixed(2), (a.y * 0.75).toFixed(1)); }
