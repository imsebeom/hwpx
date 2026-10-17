// rhwp 가 본문 문단 하나의 글자마다 준 x 위치(커서 자리)를 pt 로 찍는다. 한/글 PDF 의 글자 위치와 맞대어 본다.
//   node advances.mjs <id> <본문 문단 번호> [시작 글자=0] [개수=80]
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ED = 'C:/Users/hccga/.claude/skills/hwpx/editor/';
const m = await import(pathToFileURL(ED + 'studio-dist/node/rhwp.js').href);
m.initSync({ module: fs.readFileSync(ED + 'studio-dist/node/rhwp_bg.wasm') });
const { readZip, writeZip } = await import(pathToFileURL(ED + 'hwpx-zip.mjs').href);
const { docFontMetrics, registerInto } = await import(pathToFileURL(ED + 'font-metrics.mjs').href);

const [id, paraArg, fromArg = '0', countArg = '80'] = process.argv.slice(2);
const para = +paraArg;
const es = readZip(fs.readFileSync(path.join(HERE, 'out', 'oracle', id + '.hwpx')));
for (const e of es) if (/^Contents\/section\d+\.xml$/.test(e.name)) e.data = Buffer.from(e.data.toString('utf8').replace(/<hp:linesegarray>[\s\S]*?<\/hp:linesegarray>/g, ''), 'utf8');
const input = writeZip(es);
registerInto(m, docFontMetrics(input, m).metrics);
const doc = new m.HwpDocument(input);
const PT = 0.75; // px → pt (96dpi)
const out = [];
for (let k = +fromArg; k < +fromArg + +countArg; k++) {
  let r;
  try { r = JSON.parse(doc.getCursorRect(0, para, k)); } catch { break; }
  out.push([k, +(r.x * PT).toFixed(2), +(r.y * PT).toFixed(1)]);
}
console.log(JSON.stringify(out));
