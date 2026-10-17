// rhwp 커서 모델의 칸 목록(listId 2부터, 깊이 우선)이 XML 에서 부모가 <hp:tc> 인 <hp:subList> 의 등장 순서와
// 1:1 인지 본다. 목록마다 문단 수를 양쪽에서 세어 맞춘다.   node probe_lists.mjs <hwpx...>
import fs from 'node:fs';
import { pathToFileURL } from 'node:url';

const ED = 'C:/Users/hccga/.claude/skills/hwpx/editor/';
const m = await import(pathToFileURL(ED + 'studio-dist/node/rhwp.js').href);
m.initSync({ module: fs.readFileSync(ED + 'studio-dist/node/rhwp_bg.wasm') });
const { readZip } = await import(pathToFileURL(ED + 'hwpx-zip.mjs').href);

const TAG = /<(\/?)hp:(tc|subList|drawText|header|footer|footNote|endNote|caption|p)\b[^>]*?(\/?)>/g;

/** 부모가 칸인 subList 마다 바로 아래 문단 수(안쪽 subList 의 문단은 빼고). 구역 순서대로. */
export function xmlCellLists(buf) {
  const secs = readZip(buf, (n) => /^Contents\/section\d+\.xml$/.test(n))
    .sort((a, b) => a.name.localeCompare(b.name, 'en', { numeric: true }));
  const out = [];
  for (const s of secs) {
    const xml = s.data.toString('utf8');
    const stack = [];
    for (const x of xml.matchAll(TAG)) {
      const close = x[1] === '/', name = x[2], selfClose = x[3] === '/';
      if (name === 'p') {
        if (!close) {
          const sl = [...stack].reverse().find((e) => e.name === 'subList');
          if (sl && sl.out >= 0) out[sl.out].paras++;
        }
        continue;
      }
      if (selfClose) continue;
      if (close) { stack.pop(); continue; }
      if (name === 'subList') {
        const parent = stack.length ? stack[stack.length - 1].name : null;
        if (parent === 'tc') { stack.push({ name, out: out.length }); out.push({ paras: 0 }); }
        else stack.push({ name, out: -1 });
      } else stack.push({ name });
    }
  }
  return out;
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  let docs = 0, bad = 0;
  for (const f of process.argv.slice(2)) {
    const buf = fs.readFileSync(f);
    const doc = new m.HwpDocument(buf);
    const rl = JSON.parse(doc.getCursorModel()).lists.filter((l) => l.isCell);
    const xl = xmlCellLists(buf);
    const n = Math.min(xl.length, rl.length);
    let same = 0;
    for (let i = 0; i < n; i++) same += xl[i].paras === rl[i].paraCount;
    docs++;
    if (xl.length !== rl.length || same !== n) {
      bad++;
      const fb = [...Array(n).keys()].find((i) => xl[i].paras !== rl[i].paraCount);
      console.log(`${f.split(/[\\/]/).pop()}: XML 칸 목록 ${xl.length}, rhwp 칸 목록 ${rl.length}, 문단 수 같음 ${same}/${n}` +
        (fb !== undefined ? ` 첫 불일치 #${fb} XML ${xl[fb].paras} rhwp ${rl[fb].paraCount} host=${rl[fb].hostListId}` : ''));
    }
  }
  console.log(`문서 ${docs}, 어긋난 문서 ${bad}`);
}
