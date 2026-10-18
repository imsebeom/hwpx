// 쪽마다 첫 글(빈칸 뺀 앞 24자)을 한/글 PDF 와 rhwp(줄 배치 지운 사본)로 나란히 찍는다.
// 그림자 효과처럼 같은 글을 여러 번 그리는 문서에서 글자 겹침(pageoverlap.mjs)이 흔들릴 때 쓴다.
//   node pagestarts.mjs <정답본 id>
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';

const [id] = process.argv.slice(2);
const pdf = path.join('..', 'out', 'lab', 'hanpdf', 'rt', `${id}.pdf`);
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
const rh = [];
for (let p = 0; p < doc.pageCount(); p++) {
  const svg = doc.renderPageSvg(p);
  let pos = {};
  try { pos = JSON.parse(doc.getPositionOfPage(p)); } catch {}
  rh.push({ t: norm([...svg.matchAll(/<text\b[^>]*>([^<]*)<\/text>/g)].map((mm) => dec(mm[1])).join('')), para: pos.para });
}
const py = 'import fitz,sys,json\nsys.stdout.reconfigure(encoding="utf-8")\nd=fitz.open(sys.argv[1])\nout=[]\nfor pg in d:\n  seen=[]\n  for b in pg.get_text("dict")["blocks"]:\n    for l in b.get("lines",[]):\n      s="".join(x["text"] for x in l["spans"]).strip()\n      if s and (not seen or seen[-1]!=s): seen.append(s)\n  out.append("".join(seen))\nprint(json.dumps(out,ensure_ascii=False))';
const han = JSON.parse(execFileSync('python', ['-c', py, pdf], { encoding: 'utf8', env: { ...process.env, PYTHONIOENCODING: 'utf-8' }, maxBuffer: 1 << 28 })).map(norm);
console.log(`${id} 쪽수 한/글 ${han.length} rhwp ${rh.length}`);
for (let i = 0; i < Math.max(han.length, rh.length); i++) {
  console.log(`${String(i + 1).padStart(3)} 한/글 ${(han[i] ?? '').slice(0, 24).padEnd(24, '　')} | rhwp p${rh[i]?.para ?? '-'} ${(rh[i]?.t ?? '').slice(0, 24)}`);
}
