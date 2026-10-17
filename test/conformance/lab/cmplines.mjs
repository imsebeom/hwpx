// 한/글이 다시 저장한 실험 문서(폴더의 hwpx)마다 본문 문단의 줄 시작을 rhwp 와 맞대어 본다.
//   node cmplines.mjs <한/글 재저장 폴더> [--show]   (--show 면 줄별 글도 찍는다)
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const ED = 'C:/Users/hccga/.claude/skills/hwpx/editor/';
const m = await import(pathToFileURL(ED + 'studio-dist/node/rhwp.js').href);
m.initSync({ module: fs.readFileSync(ED + 'studio-dist/node/rhwp_bg.wasm') });
const { readZip, writeZip } = await import(pathToFileURL(ED + 'hwpx-zip.mjs').href);
const { docFontMetrics, registerInto } = await import(pathToFileURL(ED + 'font-metrics.mjs').href);

const dir = process.argv[2];
const show = process.argv.includes('--show');
let same = 0, all = 0;
for (const f of fs.readdirSync(dir).filter((x) => x.endsWith('.hwpx')).sort()) {
  const es = readZip(fs.readFileSync(path.join(dir, f)));
  const han = [];
  const texts = [];
  for (const e of es) {
    if (!/^Contents\/section\d+\.xml$/.test(e.name)) continue;
    const s = e.data.toString('utf8');
    for (const p of s.matchAll(/<hp:p\b[\s\S]*?<\/hp:p>/g)) {
      han.push([...p[0].matchAll(/<hp:lineseg\b[^>]*\btextpos="(\d+)"/g)].map((y) => +y[1]));
      texts.push([...p[0].matchAll(/<hp:t>([^<]*)<\/hp:t>/g)].map((y) => y[1]).join(''));
    }
    e.data = Buffer.from(s.replace(/<hp:linesegarray>[\s\S]*?<\/hp:linesegarray>/g, ''), 'utf8');
  }
  const input = writeZip(es);
  registerInto(m, docFontMetrics(input, m).metrics);
  const doc = new m.HwpDocument(input);
  const res = han.map((h, p) => {
    const r = JSON.parse(doc.getLineStarts(0, p));
    all++;
    const ok = h.length === r.length && h.every((v, i) => v === r[i]);
    same += ok;
    return { p, ok, h, r };
  });
  const bad = res.filter((x) => !x.ok);
  console.log(`${f.replace(/\.hwpx$/, '')} ${bad.length ? '다름' : '같음'} ${bad.map((x) => `p${x.p} 한글[${x.h}] rhwp[${x.r}]`).join(' ')}`);
  if (show) for (const x of bad) {
    // 첫 문단은 구역 정의와 단 정의 조판 부호 둘(각 8)이 앞에 있다
    const off = x.p === 0 ? 16 : 0;
    const cut = (st) => st.map((s, i) => JSON.stringify(texts[x.p].slice(Math.max(0, s - off), (st[i + 1] ?? 1e9) - off)));
    console.log('   한글', cut(x.h).join(' | '));
    console.log('   rhwp', cut(x.r).join(' | '));
  }
}
console.log(`문단 ${same}/${all} 같음`);
