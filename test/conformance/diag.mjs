// 불일치 문단 하나를 들여다본다: 한/글 줄 시작과 rhwp 줄 시작, 줄별 글, 문단 모양과 글자 모양 XML.
//   node diag.mjs <id> <문단 번호> [목록 ID]   (mismatches.jsonl 의 list. 주면 그 칸의 문단, 없으면 본문)
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ED = 'C:/Users/hccga/.claude/skills/hwpx/editor/';
const m = await import(pathToFileURL(ED + 'studio-dist/node/rhwp.js').href);
m.initSync({ module: fs.readFileSync(ED + 'studio-dist/node/rhwp_bg.wasm') });
const { readZip, writeZip } = await import(pathToFileURL(ED + 'hwpx-zip.mjs').href);
const { docFontMetrics, registerInto } = await import(pathToFileURL(ED + 'font-metrics.mjs').href);

const [id, paraArg, cellArg] = process.argv.slice(2);
const want = +paraArg;
let cellList = cellArg == null ? null : +cellArg;
const buf = fs.readFileSync(path.join(HERE, 'out', 'oracle', id + '.hwpx'));
const secs = readZip(buf, (n) => /^Contents\/section\d+\.xml$/.test(n)).sort((a, b) => a.name.localeCompare(b.name, 'en', { numeric: true }));
const header = readZip(buf, (n) => n === 'Contents/header.xml')[0].data.toString('utf8');

// 본문 문단 또는 칸 문단의 원문 XML 찾기(score.mjs 의 parseOracle 과 같은 순서)
function findPara() {
  let bodyN = 0, cellN = -1;
  for (const s of secs) {
    const xml = s.data.toString('utf8');
    // score.mjs 와 같게 모든 hp 요소를 쌓아야 칸(tc) 바로 아래 subList 만 칸으로 센다(글상자 안 subList 는 빼고)
    const TOK = /<(\/?)hp:([A-Za-z]+)\b[^>]*?(\/?)>/g;
    const stack = [];
    for (const x of xml.matchAll(TOK)) {
      const close = x[1] === '/', name = x[2], self = x[3] === '/';
      if (close) { while (stack.length) { const e = stack.pop(); if (e.name === name) break; } continue; }
      if (name === 'subList') {
        const parent = stack.length ? stack[stack.length - 1].name : null;
        const e = { name, cell: -1, k: 0 };
        if (parent === 'tc') e.cell = ++cellN;
        if (!self) stack.push(e);
        continue;
      }
      if (name === 'p') {
        const sl = [...stack].reverse().find((e) => e.name === 'subList');
        let hit = false;
        if (!sl) { hit = cellList == null && bodyN === want; bodyN++; }
        else if (sl.cell >= 0) { hit = cellList === sl.cell && sl.k === want; sl.k++; }
        if (hit) {
          // 짝이 맞는 </hp:p> 까지
          let depth = 0, i = x.index;
          const re = /<(\/?)hp:p\b[^>]*?(\/?)>/g;
          re.lastIndex = x.index;
          for (const y of xml.slice(x.index).matchAll(/<(\/?)hp:p\b[^>]*?(\/?)>/g)) {
            if (y[2] === '/') continue;
            depth += y[1] === '/' ? -1 : 1;
            if (depth === 0) return xml.slice(x.index, x.index + y.index + y[0].length);
          }
        }
        if (!self) stack.push({ name });
        continue;
      }
      if (!self) stack.push({ name });
    }
  }
  return null;
}

const es = readZip(buf);
for (const e of es) if (/^Contents\/section\d+\.xml$/.test(e.name)) e.data = Buffer.from(e.data.toString('utf8').replace(/<hp:linesegarray>[\s\S]*?<\/hp:linesegarray>/g, ''), 'utf8');
const input = writeZip(es);
registerInto(m, docFontMetrics(input, m).metrics);
const doc = new m.HwpDocument(input);
const cm = JSON.parse(doc.getCursorModel());
// 셋째 인자는 mismatches.jsonl 의 list(rhwp 목록 ID). 칸 목록 차례로 바꿔 XML 의 칸 순서와 맞춘다
const listId = cellList == null ? 0 : cellList;
if (cellList != null) cellList = (cm.lists || []).filter((l) => l.isCell).findIndex((l) => l.listId === listId);

const px = findPara();
if (!px) { console.log('문단을 못 찾음'); process.exit(1); }
// 문단 자체의 줄 배치(안쪽 표의 것은 빼려고 마지막 linesegarray 를 쓴다)
const segs = [...px.matchAll(/<hp:linesegarray>([\s\S]*?)<\/hp:linesegarray>/g)].pop()?.[1] || '';
const han = [...segs.matchAll(/<hp:lineseg\b([^>]*)\/>/g)].map((s) => Object.fromEntries([...s[1].matchAll(/(\w+)="(-?\d+)"/g)].map((a) => [a[1], +a[2]])));
const rs = JSON.parse(doc.getLineStarts(listId, want));

// 글(조판 부호는 자리 하나로 본다는 가정 없이 hp:t 만 이어 붙인다 — 부호 낀 문단은 위치가 어긋날 수 있다)
const text = [...px.replace(/<hp:linesegarray>[\s\S]*?<\/hp:linesegarray>/g, '').matchAll(/<hp:t>([^<]*)<\/hp:t>|<hp:tab\b/g)].map((y) => (y[1] ?? '\t')).join('')
  .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
const lines = (st) => st.map((s, i) => JSON.stringify(text.slice(s, st[i + 1] ?? text.length)));
console.log('한/글 줄 시작', han.map((h) => h.textpos).join(','), ' horzsize', han.map((h) => h.horzsize).join(','), ' horzpos', han.map((h) => h.horzpos).join(','));
console.log('rhwp 줄 시작', rs.join(','));
console.log('한/글 줄'); lines(han.map((h) => h.textpos)).forEach((l) => console.log('  ', l));
console.log('rhwp 줄'); lines(rs).forEach((l) => console.log('  ', l));
const pp = px.match(/paraPrIDRef="(\d+)"/)[1];
console.log('문단 모양', header.match(new RegExp(`<hh:paraPr id="${pp}"[\\s\\S]*?</hh:paraPr>`))?.[0].replace(/\s+/g, ' ').slice(0, 1200));
const cps = [...new Set([...px.matchAll(/charPrIDRef="(\d+)"/g)].map((y) => y[1]))];
for (const c of cps) console.log('글자 모양', c, header.match(new RegExp(`<hh:charPr id="${c}"[\\s\\S]*?</hh:charPr>`))?.[0].replace(/\s+/g, ' ').slice(0, 700));
console.log('원문', px.replace(/<hp:linesegarray>[\s\S]*?<\/hp:linesegarray>/g, '').slice(0, 1500));
