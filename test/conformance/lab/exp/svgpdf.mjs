// SVG 폴더(claude-linestarts CLAUDE_SVG 출력)의 쪽마다 첫 글자를 한/글 PDF 와 맞대 처음 갈리는 쪽을 찍는다.
//   node svgpdf.mjs <svg 폴더> <한/글 PDF>
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const [dir, pdf] = process.argv.slice(2);
const norm = (s) => s.replace(/\s+/g, '').replace(/[\uE000-\uF8FF]/gu, '');
const dec = (s) => s.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&amp;/g, '&');
const files = fs.readdirSync(dir).filter((f) => f.endsWith('.svg')).sort((a, b) => parseInt(a.match(/\d+/g).pop()) - parseInt(b.match(/\d+/g).pop()));
const rh = files.map((f) => {
  const svg = fs.readFileSync(path.join(dir, f), 'utf8');
  const items = [];
  for (const mm of svg.matchAll(/<text\b([^>]*)>([^<]*)<\/text>/g)) {
    const tr = /translate\(([-\d.]+),([-\d.]+)\)/.exec(mm[1]);
    const x = tr ? +tr[1] : +(/\bx="([-\d.]+)"/.exec(mm[1]) || [0, 0])[1];
    const y = tr ? +tr[2] : +(/\by="([-\d.]+)"/.exec(mm[1]) || [0, 0])[1];
    items.push([Math.round(y), x, dec(mm[2])]);
  }
  items.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  return norm(items.map((t) => t[2]).join(''));
});
const py = 'import fitz,sys,json\nsys.stdout.reconfigure(encoding="utf-8")\nd=fitz.open(sys.argv[1])\nout=[]\nfor pg in d:\n    w=sorted(pg.get_text("words"),key=lambda w:(round(w[1]),w[0]))\n    out.append("".join(x[4] for x in w))\nprint(json.dumps(out,ensure_ascii=False))';
const han = JSON.parse(execFileSync('python', ['-c', py, pdf], { encoding: 'utf8', env: { ...process.env, PYTHONIOENCODING: 'utf-8' }, maxBuffer: 1 << 28 })).map(norm);
let bad = 0;
for (let i = 0; i < Math.max(han.length, rh.length); i++) {
  const a = (han[i] ?? '').slice(0, 8);
  const b = (rh[i] ?? '').slice(0, 8);
  if (a !== b) { bad++; if (bad <= 2) console.log(`  ${i + 1}쪽 한/글 「${(han[i] ?? '').slice(0, 16)}」 rhwp 「${(rh[i] ?? '').slice(0, 16)}」`); }
}
console.log(`쪽 ${han.length}/${rh.length} 첫 글 다른 쪽 ${bad}`);
