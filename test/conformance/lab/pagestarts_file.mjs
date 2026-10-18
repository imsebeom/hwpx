// 아무 HWPX 와 그 한/글 PDF 로 쪽마다 첫 글과 끝 글(빈칸 뺀 앞뒤 16자)을 나란히 찍는다(pagestarts.mjs 의 파일판).
// 줄 배치는 그대로 둔다(--strip 이면 지운다). 회귀 코퍼스에서 바뀐 문서를 한/글과 대조할 때 쓴다.
//   node pagestarts_file.mjs <파일.hwpx> <한글.pdf> [--strip]
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';

const [file, pdf, ...rest] = process.argv.slice(2);
const E = path.join(process.env.USERPROFILE, '.claude/skills/hwpx/editor');
const dir = path.join(E, 'studio-dist', 'node');
const m = await import(pathToFileURL(path.join(dir, 'rhwp.js')).href);
m.initSync({ module: fs.readFileSync(path.join(dir, 'rhwp_bg.wasm')) });
const { docFontMetrics, registerInto } = await import(pathToFileURL(path.join(E, 'font-metrics.mjs')).href);
const { readZip, writeZip } = await import(pathToFileURL(path.join(E, 'hwpx-zip.mjs')).href);
const entries = readZip(fs.readFileSync(file));
if (rest.includes('--strip')) {
  for (const e of entries) if (/^Contents\/section\d+\.xml$/.test(e.name)) e.data = Buffer.from(e.data.toString('utf8').replace(/<hp:linesegarray>[\s\S]*?<\/hp:linesegarray>/g, ''), 'utf8');
}
const buf = writeZip(entries);
registerInto(m, docFontMetrics(buf, m).metrics);
const doc = new m.HwpDocument(buf);
const norm = (s) => s.replace(/\s+/g, '');
const dec = (s) => s.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&amp;/g, '&');
const rh = [];
for (let p = 0; p < doc.pageCount(); p++) {
  const svg = doc.renderPageSvg(p);
  rh.push(norm([...svg.matchAll(/<text\b[^>]*>([^<]*)<\/text>/g)].map((mm) => dec(mm[1])).join('')));
}
const py = 'import fitz,sys,json\nsys.stdout.reconfigure(encoding="utf-8")\nd=fitz.open(sys.argv[1])\nout=[]\nfor pg in d:\n  seen=[]\n  for b in pg.get_text("dict")["blocks"]:\n    for l in b.get("lines",[]):\n      s="".join(x["text"] for x in l["spans"]).strip()\n      if s and (not seen or seen[-1]!=s): seen.append(s)\n  out.append("".join(seen))\nprint(json.dumps(out,ensure_ascii=False))';
const han = JSON.parse(execFileSync('python', ['-c', py, pdf], { encoding: 'utf8', env: { ...process.env, PYTHONIOENCODING: 'utf-8' }, maxBuffer: 1 << 28 })).map(norm);
console.log(`쪽수 한/글 ${han.length} rhwp ${rh.length}`);
for (let i = 0; i < Math.max(han.length, rh.length); i++) {
  const h = han[i] ?? '';
  const r = rh[i] ?? '';
  const same = h.slice(0, 16) === r.slice(0, 16) && h.slice(-16) === r.slice(-16) ? '같음' : '다름';
  console.log(`${String(i + 1).padStart(3)} ${same} 한/글 ${h.slice(0, 16)} … ${h.slice(-16)}`);
  console.log(`         rhwp  ${r.slice(0, 16)} … ${r.slice(-16)}`);
}
