// 한 쪽의 글줄마다 세로 위치(px, 쪽 위 기준)를 한/글 PDF 와 rhwp(줄 배치 지운 사본)로 나란히 찍는다. 앞 6자로 짝짓는다.
//   node linecmp.mjs <정답본 id> <쪽 번호(1부터)> [한/글 PDF]
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';

const [id, pageArg, pdfArg] = process.argv.slice(2);
const pg = +pageArg - 1;
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
const norm = (s) => s.replace(/\s+/g, '');
const dec = (s) => s.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&amp;/g, '&');
const svg = doc.renderPageSvg(pg);
const items = [];
for (const mm of svg.matchAll(/<text\b([^>]*)>([^<]*)<\/text>/g)) {
  const tr = /translate\(([-\d.]+),([-\d.]+)\)/.exec(mm[1]);
  const x = tr ? +tr[1] : +(/\bx="([-\d.]+)"/.exec(mm[1]) || [0, 0])[1];
  const y = tr ? +tr[2] : +(/\by="([-\d.]+)"/.exec(mm[1]) || [0, 0])[1];
  items.push([y, x, dec(mm[2])]);
}
// 같은 기준선(1px 안)끼리 한 줄
items.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
const rl = [];
for (const it of items) {
  const last = rl[rl.length - 1];
  if (last && Math.abs(last.y - it[0]) < 1.5) last.items.push(it);
  else rl.push({ y: it[0], items: [it] });
}
const rlines = rl.map((l) => ({ y: l.y, t: norm(l.items.sort((a, b) => a[1] - b[1]).map((i) => i[2]).join('')) })).filter((l) => l.t);
const py = 'import fitz,sys,json\nsys.stdout.reconfigure(encoding="utf-8")\npg=fitz.open(sys.argv[1])[int(sys.argv[2])]\nout=[]\nfor b in pg.get_text("rawdict")["blocks"]:\n    for ln in b.get("lines",[]):\n        ch=[c for s in ln["spans"] for c in s["chars"]]\n        if ch: out.append([ch[0]["origin"][1]*96/72, "".join(c["c"] for c in ch)])\nprint(json.dumps(out,ensure_ascii=False))';
const hl = JSON.parse(execFileSync('python', ['-c', py, pdf, String(pg)], { encoding: 'utf8', env: { ...process.env, PYTHONIOENCODING: 'utf-8' }, maxBuffer: 1 << 28 }))
  .map(([y, t]) => ({ y, t: norm(t) })).filter((l) => l.t).sort((a, b) => a.y - b.y);
let ri = 0;
let prev = null;
for (const h of hl) {
  const key = h.t.slice(0, 6);
  let j = ri;
  while (j < rlines.length && !rlines[j].t.startsWith(key)) j++;
  if (j >= rlines.length) { console.log(`  한/글 ${h.y.toFixed(1)} 「${h.t.slice(0, 14)}」  rhwp 없음`); continue; }
  ri = j + 1;
  const d = rlines[j].y - h.y;
  const mark = prev != null && Math.abs(d - prev) > 0.6 ? `  <- ${(d - prev) >= 0 ? '+' : ''}${(d - prev).toFixed(1)}` : '';
  console.log(`  한/글 ${h.y.toFixed(1)} rhwp ${rlines[j].y.toFixed(1)} 차 ${d.toFixed(1)} 「${h.t.slice(0, 14)}」${mark}`);
  prev = d;
}
