// rhwp(줄 배치 지운 사본) 쪽마다 글 앞뒤와 그 쪽에 놓인 문단 번호 범위를 찍는다.
//   node pagetext.mjs <정답본 id> [쪽 번호(1부터) ...]
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const [id, ...want] = process.argv.slice(2);
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
const pages = want.length ? want.map(Number) : [...Array(doc.pageCount()).keys()].map((i) => i + 1);
for (const p of pages) {
  const t = doc.getPageText(p - 1);
  let first = null;
  try { first = JSON.parse(doc.getPositionOfPage(p - 1)); } catch {}
  const s = String(t).replace(/\s+/g, ' ');
  console.log(`== rhwp ${p}쪽 (${s.length}자) 첫 위치 ${JSON.stringify(first)} ${s.slice(0, 160)}`);
  console.log(`   ... 끝: ${s.slice(-160)}`);
}
