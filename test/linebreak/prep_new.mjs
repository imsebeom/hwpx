// 에디터 서버(editorBytes)와 같은 전처리를 거친 사본을 만든다: node prep.mjs <목록.txt> <출력폴더> <새목록.txt>
// 고칠 것이 없으면 원본 경로를 그대로 적는다. 새목록은 「전처리본\t원본」 줄이다
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
const ED = 'C:/Users/hccga/.claude/skills/hwpx/editor/';
const { readZip, stripDummyLinesegs } = await import(pathToFileURL(ED + 'hwpx-zip.mjs').href);
const { rhwpLayout } = await import(pathToFileURL(ED + 'rhwp_layout.mjs').href);
const [list, outDir, newList] = process.argv.slice(2);
fs.mkdirSync(outDir, { recursive: true });
function lacks(buf) {
  const entries = readZip(buf, (n) => /^Contents\/section\d+\.xml$/.test(n)) || [];
  for (const e of entries) {
    const xml = e.data.toString('utf8');
    const paras = (xml.match(/<hp:p\b/g) || []).length;
    const segs = (xml.match(/<hp:linesegarray\b/g) || []).length;
    if (segs < paras && /<hp:tbl\b[^>]*>\s*<hp:sz\b[^>]*\/>\s*<hp:pos\b[^>]*treatAsChar="1"/.test(xml)) return true;
  }
  return false;
}
const lines = [];
let i = 0, prepped = 0;
for (const f of fs.readFileSync(list, 'utf8').split(/\r?\n/).filter(Boolean)) {
  i++;
  let raw;
  try { raw = fs.readFileSync(f); } catch { continue; }
  let buf = raw;
  try {
    const st = stripDummyLinesegs(raw);
    if (st.removed || lacks(raw)) {
      try { buf = (await rhwpLayout(raw)).buf; } catch { buf = st.buf; }
    }
  } catch { /* zip 아님 등 — 원본 그대로 */ }
  if (buf !== raw) {
    const p = path.join(outDir, `p${i}.hwpx`).replace(/\\/g, '/');
    fs.writeFileSync(p, buf);
    lines.push(`${p}\t${f}`);
    prepped++;
  } else lines.push(`${f}\t${f}`);
}
fs.writeFileSync(newList, lines.join('\n'));
console.log('files', lines.length, 'prepped', prepped);
