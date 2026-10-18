// 쪽마다 글자 집합(빈칸 뺀 글자 개수)의 겹침을 한/글 PDF 와 rhwp(줄 배치 지운 사본)로 맞대 처음 갈리는 쪽을 찾는다.
// 표가 쪽 머리에 오면 글 읽기 순서가 달라 첫 글 비교(pagecmp.mjs)가 흔들리는 것을 피한다.
//   node pageoverlap.mjs <정답본 id> [한/글 PDF]
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';

const [id, pdfArg] = process.argv.slice(2);
const pdf = pdfArg || path.join('..', 'out', 'lab', 'hanpdf', 'rt', `${id}.pdf`);
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
const norm = (s) => s.replace(/\s+/g, '').replace(/[-]/gu, '');
const dec = (s) => s.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&amp;/g, '&');
const rh = [];
for (let p = 0; p < doc.pageCount(); p++) {
  const svg = doc.renderPageSvg(p);
  rh.push(norm([...svg.matchAll(/<text\b[^>]*>([^<]*)<\/text>/g)].map((mm) => dec(mm[1])).join('')));
}
const py = 'import fitz,sys,json\nsys.stdout.reconfigure(encoding="utf-8")\nd=fitz.open(sys.argv[1])\nprint(json.dumps([pg.get_text() for pg in d],ensure_ascii=False))';
const han = JSON.parse(execFileSync('python', ['-c', py, pdf], { encoding: 'utf8', env: { ...process.env, PYTHONIOENCODING: 'utf-8' }, maxBuffer: 1 << 28 })).map(norm);
const bag = (s) => { const b = new Map(); for (const ch of s) b.set(ch, (b.get(ch) ?? 0) + 1); return b; };
const overlap = (a, b) => { const A = bag(a); const B = bag(b); let common = 0; for (const [k, v] of A) common += Math.min(v, B.get(k) ?? 0); return common / Math.max(1, Math.max(a.length, b.length)); };
console.log(`${id} 쪽수 한/글 ${han.length} rhwp ${rh.length}`);
for (let i = 0; i < Math.max(han.length, rh.length); i++) {
  const o = overlap(han[i] ?? '', rh[i] ?? '');
  if (o < 0.9) { console.log(`  처음 갈리는 쪽 ${i + 1}: 겹침 ${(o * 100).toFixed(0)}% 글자 한/글 ${(han[i] ?? '').length} rhwp ${(rh[i] ?? '').length}`); break; }
}
