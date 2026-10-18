// 쪽마다 처음 글자(빈칸 뺀 앞 16자)를 한/글 PDF 와 rhwp(줄 배치 지운 사본, 채점기와 같은 조건)로 맞대어 처음 갈리는 쪽을 찾는다.
//   node pagecmp.mjs <정답본 id> [한/글 PDF=../out/lab/hanpdf/rt/<id>.pdf]
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';

const [src, pdfArg] = process.argv.slice(2); const id = src;
const pdf = pdfArg || path.join('..', 'out', 'lab', 'hanpdf', 'rt', `${id}.pdf`);
const E = path.join(process.env.USERPROFILE, '.claude/skills/hwpx/editor');
const dir = path.join(E, 'studio-dist', 'node');
const m = await import(pathToFileURL(path.join(dir, 'rhwp.js')).href);
m.initSync({ module: fs.readFileSync(path.join(dir, 'rhwp_bg.wasm')) });
const { docFontMetrics, registerInto } = await import(pathToFileURL(path.join(E, 'font-metrics.mjs')).href);
const { readZip, writeZip } = await import(pathToFileURL(path.join(E, 'hwpx-zip.mjs')).href);
const buf = fs.readFileSync(src);


try { registerInto(m, docFontMetrics(buf, m).metrics); } catch (e) { console.error('metrics', e.message); }
const doc = new m.HwpDocument(buf);
const norm = (s) => s.replace(/\s+/g, '').replace(/[\uE000-\uF8FF\u{F0000}-\u{FFFFD}]/gu, '');
const dec = (s) => s.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&amp;/g, '&');
const rh = [];
for (let p = 0; p < doc.pageCount(); p++) {
  const svg = doc.renderPageSvg(p);
  // 글자는 <text> 마다 하나(또는 몇 개)라 y, x 차례로 다시 늘어놓는다
  const items = [];
  for (const mm of svg.matchAll(/<text\b([^>]*)>([^<]*)<\/text>/g)) {
    const tr = /translate\(([-\d.]+),([-\d.]+)\)/.exec(mm[1]);
    const x = tr ? +tr[1] : +(/\bx="([-\d.]+)"/.exec(mm[1]) || [0, 0])[1];
    const y = tr ? +tr[2] : +(/\by="([-\d.]+)"/.exec(mm[1]) || [0, 0])[1];
    items.push([Math.round(y), x, dec(mm[2])]);
  }
  items.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  rh.push(norm(items.map((t) => t[2]).join('')));
}
const py = 'import fitz,sys,json\nsys.stdout.reconfigure(encoding="utf-8")\nd=fitz.open(sys.argv[1])\nout=[]\nfor pg in d:\n    w=sorted(pg.get_text("words"),key=lambda w:(round(w[1]),w[0]))\n    out.append("".join(x[4] for x in w))\nprint(json.dumps(out,ensure_ascii=False))';
const han = JSON.parse(execFileSync('python', ['-c', py, pdf], { encoding: 'utf8', env: { ...process.env, PYTHONIOENCODING: 'utf-8' }, maxBuffer: 1 << 28 })).map(norm);
console.log(`${id} 쪽수 한/글 ${han.length} rhwp ${rh.length}`);
const n = Math.max(han.length, rh.length);
let shown = 0;
for (let i = 0; i < n && shown < 99; i++) {
  const a = (han[i] ?? '').slice(0, 16);
  const b = (rh[i] ?? '').slice(0, 16);
  // 쪽 머리의 앞 글이 같은지(꼬리말 쪽 번호 등은 처음 16자 밖이라 대개 영향 없음)
  if (a.slice(0, 8) !== b.slice(0, 8)) {
    console.log(`  ${i + 1}쪽 첫 글  한/글 「${a}」  rhwp 「${b}」`);
    if (i > 0) console.log(`  ${i}쪽 끝 글  한/글 「${(han[i - 1] ?? '').slice(-16)}」  rhwp 「${(rh[i - 1] ?? '').slice(-16)}」`);
    shown++;
    break;
  }
}
if (!shown) console.log('  쪽 첫 글이 모두 같다');
