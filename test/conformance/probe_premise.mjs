// 채점 전제 확인: rhwp 가 저장된 줄 배치를 믿는가, 지우고 넣으면 자기가 계산한 줄 배치를 내보내는가.
//   node probe_premise.mjs <한글이 저장한 hwpx>
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const ED = 'C:/Users/hccga/.claude/skills/hwpx/editor/';
const m = await import(pathToFileURL(ED + 'studio-dist/node/rhwp.js').href);
m.initSync({ module: fs.readFileSync(ED + 'studio-dist/node/rhwp_bg.wasm') });
const { readZip, writeZip } = await import(pathToFileURL(ED + 'hwpx-zip.mjs').href);

const SEG = /<hp:linesegarray>[\s\S]*?<\/hp:linesegarray>/g;
const sec = (buf) => readZip(buf, (n) => n === 'Contents/section0.xml')[0].data.toString('utf8');
const starts = (xml) => [...xml.matchAll(SEG)].map((x) => [...x[0].matchAll(/textpos="(\d+)"/g)].map((t) => +t[1]).join(','));
const strip = (buf) => {
  const es = readZip(buf);
  for (const e of es) if (/^Contents\/section\d+\.xml$/.test(e.name)) e.data = Buffer.from(e.data.toString('utf8').replace(SEG, ''), 'utf8');
  return writeZip(es);
};

const orig = fs.readFileSync(process.argv[2]);
const han = starts(sec(orig));
const keep = starts(sec(Buffer.from(new m.HwpDocument(orig).exportHwpx())));
const d1 = new m.HwpDocument(strip(orig)); const n1 = d1.reflowLinesegs();
const own = starts(sec(Buffer.from(d1.exportHwpx())));
const d2 = new m.HwpDocument(orig); const n2 = d2.reflowLinesegs();
const kept2 = starts(sec(Buffer.from(d2.exportHwpx())));
console.log(`reflow 문단 수: 지운 문서 ${n1}, 기록 둔 문서 ${n2}. 기록 둔 문서 reflow 뒤 한글과 같은 문단 ${kept2.filter((x, i) => x === han[i]).length}/${han.length}`);
const same = (a, b) => a.filter((x, i) => x === b[i]).length;
console.log(`한글 문단 ${han.length}, 기록 둔 채 내보냄 ${keep.length}(한글과 같은 문단 ${same(han, keep)}), 지우고 내보냄 ${own.length}(한글과 같은 문단 ${same(han, own)})`);
const diff = han.map((h, i) => [i, h, own[i]]).filter(([, h, o]) => h !== o).slice(0, 5);
for (const [i, h, o] of diff) console.log(`  문단 ${i}: 한글 [${h}] / rhwp [${o}]`);
