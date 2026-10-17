// pdfadv.py 의 rhwp 판: 폴더의 hwpx 마다 본문 문단의 글자 종류별 전진 폭(pt, 커서 x 차)과 줄마다 글자 수.
//   node rhwpadv.mjs <hwpx 폴더> [출력.json]
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const ED = 'C:/Users/hccga/.claude/skills/hwpx/editor/';
const m = await import(pathToFileURL(ED + 'studio-dist/node/rhwp.js').href);
m.initSync({ module: fs.readFileSync(ED + 'studio-dist/node/rhwp_bg.wasm') });
const { readZip, writeZip } = await import(pathToFileURL(ED + 'hwpx-zip.mjs').href);
const { docFontMetrics, registerInto } = await import(pathToFileURL(ED + 'font-metrics.mjs').href);

const dir = process.argv[2];
const res = {};
const median = (a) => { const s = [...a].sort((x, y) => x - y); return s.length ? +s[Math.floor(s.length / 2)].toFixed(3) : null; };
for (const f of fs.readdirSync(dir).filter((x) => x.endsWith('.hwpx')).sort()) {
  const es = readZip(fs.readFileSync(path.join(dir, f)));
  let text = [];
  for (const e of es) {
    if (!/^Contents\/section\d+\.xml$/.test(e.name)) continue;
    const s = e.data.toString('utf8').replace(/<hp:linesegarray>[\s\S]*?<\/hp:linesegarray>/g, '');
    e.data = Buffer.from(s, 'utf8');
    text = [...s.matchAll(/<hp:p\b[\s\S]*?<\/hp:p>/g)].map((p) => [...p[0].matchAll(/<hp:t>([^<]*)<\/hp:t>/g)].map((t) => t[1]).join('')
      .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&amp;/g, '&'));
  }
  const input = writeZip(es);
  registerInto(m, docFontMetrics(input, m).metrics);
  const doc = new m.HwpDocument(input);
  const adv = {};
  const lines = [];
  text.forEach((t, p) => {
    const xs = [];
    for (let k = 0; k <= t.length; k++) xs.push(JSON.parse(doc.getCursorRect(0, p, k)));
    for (let k = 0; k < t.length; k++) {
      if (xs[k + 1].y !== xs[k].y) continue; // 줄이 바뀐 자리
      (adv[t[k]] ??= []).push((xs[k + 1].x - xs[k].x) * 0.75);
    }
    const st = JSON.parse(doc.getLineStarts(0, p));
    st.forEach((s, i) => lines.push((st[i + 1] ?? t.length) - s));
  });
  const pick = Object.fromEntries(Object.entries(adv).filter(([k]) => process.env.ALL || '가 a0.'.includes(k)).map(([k, v]) => [k, median(v)]));
  res[f.replace(/\.hwpx$/, '')] = { adv: pick, lines };
  console.log(f.replace(/\.hwpx$/, ''), JSON.stringify(pick), JSON.stringify(lines));
}
if (process.argv[3]) fs.writeFileSync(process.argv[3], JSON.stringify(res, null, 1));
