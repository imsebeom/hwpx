/**
 * 한글이 없을 때 rhwp 로 표 높이를 보정한다(server.mjs 가 한글 줄 배치에 실패하면 쓴다).
 *
 *   node rhwp_layout.mjs <in.hwpx> <out.hwpx>
 *
 * 스킬 산출물은 모든 문단에 한 줄짜리 더미 줄 배치를 달고 표 높이(hp:tbl/hp:sz height)를 한 줄 기준으로 적는다.
 * 더미를 걷어도 rhwp 는 글자처럼 취급하는 표(treatAsChar="1")에서 「내용이 적힌 높이의 1.5배 이하로 넘치면 적힌
 * 높이로 비례 축소」 규칙(height_measurer.rs TAC_SHRINK)을 적용하는데, 줄 배치가 없으면 행마다 줄일 수 있는 하한이 0 이라
 * 두 줄이 한 줄 칸에 눌리고 아래 표와 겹친다(edwardkim/rhwp#7419).
 * 적힌 높이가 0 이면 이 규칙이 걸리지 않아 행이 내용만큼 늘지만, 쪽 나누기가 그 표를 높이 0 으로 보아 쪽 밖으로 밀어낸다.
 * 그래서 두 번 연다 — ① 표 높이를 0 으로 두고 rhwp 가 내용으로 잰 표 높이를 얻고 ② 그 값을 적어 넘긴다.
 * 적힌 높이와 내용이 같아져 축소도 늘림도 일어나지 않는다. 한글은 이 값을 다시 계산하므로 한글 결과는 원본과 같다
 * (2026-09-25 문항 3, 한글 PDF 6쪽 픽셀 동일. rhwp 에서는 표가 한글 재저장본과 같은 쪽에 놓인다).
 * 셀 안의 표는 건드리지 않는다.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { readZip, writeZip, stripDummyLinesegs } from './hwpx-zip.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
let HwpDocument = null;

async function engine() {
  if (HwpDocument) return HwpDocument;
  const dir = path.join(HERE, 'studio-dist', 'node');   // setup.mjs 가 번들과 같은 WASM 을 둔다
  const m = await import(pathToFileURL(path.join(dir, 'rhwp.js')).href);
  m.initSync({ module: fs.readFileSync(path.join(dir, 'rhwp_bg.wasm')) });
  return (HwpDocument = m.HwpDocument);
}

/** section XML 의 본문(깊이 0) 표 여는 태그 위치. */
function bodyTables(xml) {
  const out = [];
  let depth = 0;
  for (const m of xml.matchAll(/<hp:tbl\b[^>]*>|<\/hp:tbl>/g)) {
    if (m[0].startsWith('</')) { depth--; continue; }
    if (depth === 0) out.push(m.index);
    depth++;
  }
  return out;
}

/** 본문 표 i 번째의 hp:sz height 를 heights[i] 로(글자처럼 취급하는 표만, null 은 그대로). 바꾼 수도 돌려준다. */
function setHeights(xml, heights) {
  const pos = bodyTables(xml);
  let res = xml, changed = 0;
  for (let i = pos.length - 1; i >= 0; i--) {
    if (heights[i] == null) continue;
    const start = pos[i];
    const posAt = res.indexOf('<hp:pos ', start);
    if (posAt < 0 || !/^<hp:pos [^>]*treatAsChar="1"/.test(res.slice(posAt, posAt + 300))) continue;
    const szAt = res.indexOf('<hp:sz ', start);
    const szEnd = res.indexOf('/>', szAt);
    res = res.slice(0, szAt) + res.slice(szAt, szEnd).replace(/height="\d+"/, `height="${heights[i]}"`) + res.slice(szEnd);
    changed++;
  }
  return { xml: res, changed };
}

/** 반환: { buf, tables } — 고칠 표가 없으면 더미만 걷은 buf, tables 0. */
export async function rhwpLayout(input) {
  const Doc = await engine();
  const entries = readZip(stripDummyLinesegs(input).buf);
  const secs = entries.filter((e) => /^Contents\/section\d+\.xml$/.test(e.name))
    .sort((a, b) => Number(a.name.match(/\d+/)[0]) - Number(b.name.match(/\d+/)[0]));
  const orig = secs.map((e) => e.data.toString('utf8'));
  const counts = orig.map((x) => bodyTables(x).length);

  // ① 높이 0 으로 열어 잰다
  let zeroed = 0;
  secs.forEach((e, s) => {
    const r = setHeights(orig[s], Array(counts[s]).fill(0));
    zeroed += r.changed;
    e.data = Buffer.from(r.xml, 'utf8');
  });
  if (!zeroed) { secs.forEach((e, s) => { e.data = Buffer.from(orig[s], 'utf8'); }); return { buf: writeZip(entries), tables: 0 }; }
  const doc = new Doc(new Uint8Array(writeZip(entries)));
  const secCount = doc.getSectionCount();
  const ctrls = JSON.parse(doc.getControls()).filter((c) => c.ctrlId === 'tbl' && c.list < secCount);
  const heights = counts.map(() => []);
  for (const c of ctrls) {
    let boxes;
    try { boxes = JSON.parse(doc.getTableCellBboxes(c.list, c.para, c.controlIndex)); } catch { continue; }   // 본문 표가 아니다
    const rows = new Map();   // 행마다 rowSpan 1 칸의 가장 큰 높이. 쪽을 넘는 행은 조각을 따로 센다
    for (const b of boxes) {
      if (b.rowSpan !== 1) continue;
      const k = `${b.row}@${b.pageIndex}`;
      rows.set(k, Math.max(rows.get(k) ?? 0, b.h));
    }
    heights[c.list].push(Math.round([...rows.values()].reduce((a, b) => a + b, 0) * 75));   // px → HWPUNIT(96dpi)
  }
  doc.free?.();
  heights.forEach((h, s) => { if (h.length !== counts[s]) throw new Error(`section${s} 표 수가 맞지 않는다(${h.length}/${counts[s]})`); });

  // ② 잰 높이를 적는다
  let tables = 0;
  secs.forEach((e, s) => {
    const r = setHeights(orig[s], heights[s]);
    tables += r.changed;
    e.data = Buffer.from(r.xml, 'utf8');
  });
  return { buf: writeZip(entries), tables };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [inp, outp] = process.argv.slice(2);
  if (!inp || !outp) { console.error('사용법: node rhwp_layout.mjs <in.hwpx> <out.hwpx>'); process.exit(2); }
  const r = await rhwpLayout(fs.readFileSync(inp));
  fs.writeFileSync(outp, r.buf);
  console.log(`표 높이 보정 ${r.tables}개: ${outp}`);
}
