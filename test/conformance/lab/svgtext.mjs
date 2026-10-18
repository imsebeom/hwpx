// rhwp(줄 배치 지운 사본) 한 쪽의 글 조각을 세로 위치 순으로 찍는다.
//   node svgtext.mjs <정답본 id> <쪽 번호(1부터)> [y 이상] [y 이하]
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const [id, pageArg, lo = '0', hi = '99999'] = process.argv.slice(2);
const E = path.join(process.env.USERPROFILE, '.claude/skills/hwpx/editor');
const dir = path.join(E, 'studio-dist', 'node');
const m = await import(pathToFileURL(path.join(dir, 'rhwp.js')).href);
m.initSync({ module: fs.readFileSync(path.join(dir, 'rhwp_bg.wasm')) });
const { docFontMetrics, registerInto } = await import(pathToFileURL(path.join(E, 'font-metrics.mjs')).href);
const { readZip, writeZip } = await import(pathToFileURL(path.join(E, 'hwpx-zip.mjs')).href);
const entries = readZip(fs.readFileSync(path.join('..', 'out', 'oracle', `${id}.hwpx`)));
for (const e of entries) if (/^Contents\/section\d+\.xml$/.test(e.name)) e.data = Buffer.from(e.data.toString('utf8').replace(/<hp:linesegarray>[\s\S]*?<\/hp:linesegarray>/g, ''), 'utf8');
const buf = writeZip(entries);
registerInto(m, docFontMetrics(buf, m).metrics);
const doc = new m.HwpDocument(buf);
const svg = doc.renderPageSvg(Number(pageArg) - 1);
const rows = new Map();
for (const mm of svg.matchAll(/<text\b([^>]*)>([^<]*)<\/text>/g)) {
  const y = Number((/\by="([-\d.]+)"/.exec(mm[1]) ?? [])[1]);
  const x = Number((/\bx="([-\d.]+)"/.exec(mm[1]) ?? [])[1]);
  if (!(y >= Number(lo) && y <= Number(hi))) continue;
  const k = y.toFixed(1);
  if (!rows.has(k)) rows.set(k, []);
  rows.get(k).push([x, mm[2]]);
}
for (const [y, parts] of [...rows].sort((a, b) => Number(a[0]) - Number(b[0]))) {
  console.log(y.padStart(7), parts.sort((a, b) => a[0] - b[0]).map((p) => p[1]).join(''));
}
