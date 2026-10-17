// 칸 문단 줄 시작이 비어 나오는 것이 지연 계산 때문인지 본다: 그리기 전 / 모든 쪽을 그린 뒤 / reflowLinesegs 뒤.
//   node probe_lazy.mjs <정답본 hwpx> <listId> <para>
import fs from 'node:fs';
import { pathToFileURL } from 'node:url';

const ED = 'C:/Users/hccga/.claude/skills/hwpx/editor/';
const m = await import(pathToFileURL(ED + 'studio-dist/node/rhwp.js').href);
m.initSync({ module: fs.readFileSync(ED + 'studio-dist/node/rhwp_bg.wasm') });
const { readZip, writeZip } = await import(pathToFileURL(ED + 'hwpx-zip.mjs').href);
const SEG = /<hp:linesegarray>[\s\S]*?<\/hp:linesegarray>/g;
const [file, list, para] = process.argv.slice(2);
const es = readZip(fs.readFileSync(file));
for (const e of es) if (/^Contents\/section\d+\.xml$/.test(e.name)) e.data = Buffer.from(e.data.toString('utf8').replace(SEG, ''), 'utf8');
const buf = writeZip(es);

const empties = (doc) => {
  const cm = JSON.parse(doc.getCursorModel());
  let e = 0, t = 0;
  for (const l of cm.lists.filter((x) => x.isCell)) for (let k = 0; k < l.paraCount; k++) { t++; if (doc.getLineStarts(l.listId, k) === '[]') e++; }
  return `${e}/${t}`;
};
const a = new m.HwpDocument(buf);
console.log('그리기 전', a.getLineStarts(+list, +para), '빈 칸 문단', empties(a));
for (let p = 0; p < a.pageCount(); p++) a.getPageTextLayout(p);
console.log('모든 쪽 그린 뒤', a.getLineStarts(+list, +para), '빈 칸 문단', empties(a));
const b = new m.HwpDocument(buf);
const n = b.reflowLinesegs();
console.log(`reflowLinesegs(${n}) 뒤`, b.getLineStarts(+list, +para), '빈 칸 문단', empties(b));
