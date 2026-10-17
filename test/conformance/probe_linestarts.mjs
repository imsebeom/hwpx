// getLineStarts 가 한글 줄 배치(textpos)와 같은 눈금인지 본다. 본문(구역 0) 문단만.
//   node probe_linestarts.mjs <한글이 저장한 hwpx>
import fs from 'node:fs';
import { pathToFileURL } from 'node:url';

const ED = 'C:/Users/hccga/.claude/skills/hwpx/editor/';
const m = await import(pathToFileURL(ED + 'studio-dist/node/rhwp.js').href);
m.initSync({ module: fs.readFileSync(ED + 'studio-dist/node/rhwp_bg.wasm') });
const { readZip, writeZip } = await import(pathToFileURL(ED + 'hwpx-zip.mjs').href);
const SEG = /<hp:linesegarray>[\s\S]*?<\/hp:linesegarray>/g;

// 한글 정답: 구역 0 최상위 문단(subList 밖)의 textpos 목록
function topParas(xml) {
  const out = [];
  let depth = 0, start = -1;
  for (const x of xml.matchAll(/<hp:p\b|<\/hp:p>|<hp:subList\b|<\/hp:subList>/g)) {
    const t = x[0];
    if (t === '<hp:subList') depth++;
    else if (t === '</hp:subList>') depth--;
    else if (t === '<hp:p' && depth === 0) start = x.index;
    else if (t === '</hp:p>' && depth === 0 && start >= 0) { out.push(xml.slice(start, x.index)); start = -1; }
  }
  return out.map((p) => {
    // 문단 끝의 linesegarray 만(안에 든 표 문단의 것은 subList 안이라 제외: 마지막 것)
    const segs = [...p.matchAll(/<hp:linesegarray>([\s\S]*?)<\/hp:linesegarray>/g)];
    const last = segs.length ? segs[segs.length - 1][1] : '';
    return [...last.matchAll(/textpos="(\d+)"/g)].map((t) => +t[1]);
  });
}

const orig = fs.readFileSync(process.argv[2]);
const xml = readZip(orig, (n) => n === 'Contents/section0.xml')[0].data.toString('utf8');
const han = topParas(xml);
const es = readZip(orig);
for (const e of es) if (/^Contents\/section\d+\.xml$/.test(e.name)) e.data = Buffer.from(e.data.toString('utf8').replace(SEG, ''), 'utf8');
const doc = new m.HwpDocument(writeZip(es));
const n = doc.getParagraphCount(0);
let same = 0, multi = 0, multiSame = 0;
const bad = [];
for (let p = 0; p < Math.min(n, han.length); p++) {
  const r = JSON.parse(doc.getLineStarts(0, p));
  const ok = JSON.stringify(r) === JSON.stringify(han[p]);
  same += ok;
  if (han[p].length > 1) { multi++; multiSame += ok; }
  if (!ok && bad.length < 5) bad.push(`문단 ${p}: 한글 [${han[p]}] / rhwp [${r}]`);
}
console.log(`문단 rhwp ${n} 한글 ${han.length}, 같음 ${same}, 여러 줄 문단 ${multi} 중 같음 ${multiSame}`);
bad.forEach((b) => console.log('  ' + b));
