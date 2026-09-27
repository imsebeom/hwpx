// 편집 흐름 회귀 시험. 에디터 엔진(studio-dist/node)으로 문서를 열어, 본문 글자처럼 취급 표마다 칸 편집을 해 보고
// 표 높이가 따라가는지, 쪽 끝을 넘거나 표와 겹치는 글 줄이 생기는지, 되돌린 뒤 원래대로인지 본다.
//   node editor/tests/edit_flow.mjs <문서.hwpx> [--verbose]
// 시험 종류: ① 칸 끝에 두 줄 넣기/지우기(미룬 쪽 나누기) ② 칸 Enter 두 번/합치기 ③ 칸 글자 16pt ④ 칸 안 그림 넣기
//          ⑤ 본문 그림 문단 넣기(문서 전체에서 5곳)
// 판정: 처음에 없던 넘침, 겹침이 생기면 실패. ①②는 되돌린 뒤 표 높이가 처음과 1px 안인지도 본다.
// 비례 축소로 처음부터 눌려 그려지던 표는 되돌린 뒤 실제 내용 높이로 커질 수 있다(실패로 치지 않고 「바로잡힘」으로 적는다).
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const dir = path.join(HERE, '..', 'studio-dist', 'node');
const m = await import(pathToFileURL(path.join(dir, 'rhwp.js')).href);
m.initSync({ module: fs.readFileSync(path.join(dir, 'rhwp_bg.wasm')) });

const file = process.argv[2];
const verbose = process.argv.includes('--verbose');
if (!file) { console.error('사용법: node edit_flow.mjs <문서.hwpx> [--verbose]'); process.exit(2); }
const bytes = fs.readFileSync(file);
const LINE = '가나다라 마바사아 자차카타 파하가나 다라마바 사아자차 카타파하 가나다라 마바사아 자차카타 '.repeat(2);
// 1×1 흰 PNG
const PNG = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==', 'base64');

function problems(doc) {
  let over = 0, overlap = 0;
  for (let pg = 0; pg < doc.pageCount(); pg++) {
    const info = JSON.parse(doc.getPageInfo(pg));
    let l = doc.getPageControlLayout(pg); l = typeof l === 'string' ? JSON.parse(l) : l;
    const boxes = l.controls.filter((c) => c.type === 'table');
    for (const r of JSON.parse(doc.getPageTextLayout(pg)).runs.filter((r) => !r.cellPath && r.w >= 1)) {
      if (r.y + r.h > info.footerArea.y + 1) over++;
      if (boxes.some((t) => r.y + r.h > t.y + 1 && r.y < t.y + t.h - 1 && r.x < t.x + t.w && r.x + r.w > t.x)) overlap++;
    }
  }
  return { over, overlap };
}
function tables(doc) {
  const out = [];
  for (let p = 0; p < doc.getParagraphCount(0); p++) {
    for (let c = 0; c < 4; c++) {
      try {
        const d = JSON.parse(doc.getTableDimensions(0, p, c));
        if (d.cellCount && JSON.parse(doc.getTableProperties(0, p, c)).treatAsChar) out.push({ p, c });
      } catch { /* 표 아님 */ }
    }
  }
  return out;
}
function height(doc, t) {
  for (let pg = 0; pg < doc.pageCount(); pg++) {
    try { const b = JSON.parse(doc.getTableBBoxAtPage(0, t.p, t.c, pg)); if (b?.height) return b.height; } catch { /* 이 쪽에 없음 */ }
  }
  return NaN;
}

const base = problems(new m.HwpDocument(bytes));
let fails = 0, fixed = 0;
const report = (name, t, ok, detail) => {
  if (!ok) fails++;
  if (!ok || verbose) console.log(`${ok ? '통과' : '실패'} ${name} p${t.p}: ${detail}`);
};
const worse = (p) => p.over > base.over || p.overlap > base.overlap;

for (const t of tables(new m.HwpDocument(bytes))) {
  // ① 넣기/지우기
  {
    const doc = new m.HwpDocument(bytes);
    const h0 = height(doc, t);
    const len = doc.getCellParagraphLength(0, t.p, t.c, 0, 0);
    doc.insertTextInCellDeferredPagination(0, t.p, t.c, 0, 0, len, LINE); doc.flushDeferredPagination();
    const h1 = height(doc, t), p1 = problems(doc);
    doc.deleteTextInCellDeferredPagination(0, t.p, t.c, 0, 0, len, [...LINE].length); doc.flushDeferredPagination();
    const h2 = height(doc, t), p2 = problems(doc);
    const back = Math.abs(h2 - h0) <= 1;
    if (!back && h2 > h0) fixed++;
    report('넣기/지우기', t, !worse(p1) && !worse(p2) && h1 > h0 - 0.5,
      `높이 ${h0.toFixed(1)} → ${h1.toFixed(1)} → ${h2.toFixed(1)}${back ? '' : '(바로잡힘)'} 넘침 ${p1.over}/${p2.over} 겹침 ${p1.overlap}/${p2.overlap}`);
  }
  // ② Enter/합치기
  {
    const doc = new m.HwpDocument(bytes);
    const h0 = height(doc, t);
    const len = doc.getCellParagraphLength(0, t.p, t.c, 0, 0);
    doc.splitParagraphInCell(0, t.p, t.c, 0, 0, len);
    doc.splitParagraphInCell(0, t.p, t.c, 0, 1, 0);
    const h1 = height(doc, t), p1 = problems(doc);
    doc.mergeParagraphInCell(0, t.p, t.c, 0, 2);
    doc.mergeParagraphInCell(0, t.p, t.c, 0, 1);
    const h2 = height(doc, t), p2 = problems(doc);
    report('Enter/합치기', t, !worse(p1) && !worse(p2) && h1 > h0 + 1, `높이 ${h0.toFixed(1)} → ${h1.toFixed(1)} → ${h2.toFixed(1)} 넘침 ${p1.over}/${p2.over}`);
  }
  // ③ 글자 16pt
  {
    const doc = new m.HwpDocument(bytes);
    const len = doc.getCellParagraphLength(0, t.p, t.c, 0, 0);
    if (len > 0) {
      doc.applyCharFormatInCell(0, t.p, t.c, 0, 0, 0, len, JSON.stringify({ fontSize: 1600 }));
      const p1 = problems(doc);
      report('글자 16pt', t, !worse(p1), `넘침 ${p1.over} 겹침 ${p1.overlap}`);
    }
  }
  // ④ 칸 안 그림(20mm) — cli image 와 같게 칸 첫 문단 뒤에 새 문단을 만들어 넣는다
  {
    const doc = new m.HwpDocument(bytes);
    const h0 = height(doc, t);
    const len = doc.getCellParagraphLength(0, t.p, t.c, 0, 0);
    doc.splitParagraphInCell(0, t.p, t.c, 0, 0, len);
    const w = Math.round((20 * 7200) / 25.4);
    const r = JSON.parse(doc.insertPictureEx(JSON.stringify({
      sectionIdx: 0, paraIdx: t.p, charOffset: 0,
      cellPath: JSON.stringify([{ controlIndex: t.c, cellIndex: 0, cellParaIndex: 1 }]),
      width: w, height: w, naturalWidthPx: 1, naturalHeightPx: 1, extension: 'png', description: '',
      paperOffsetXHu: -2147483648, paperOffsetYHu: 0,
    }), PNG));
    const h1 = height(doc, t), p1 = problems(doc);
    report('칸 그림', t, r.ok && !worse(p1) && h1 >= h0, `높이 ${h0.toFixed(1)} → ${h1.toFixed(1)} 넘침 ${p1.over} 겹침 ${p1.overlap}`);
  }
}
// ⑤ 본문 그림(40mm): 문단마다 뒤에 그림 문단을 넣어 본다(글 있는 문단 가운데 5곳)
{
  const probe = new m.HwpDocument(bytes);
  const n = probe.getParagraphCount(0);
  const picks = [];
  for (let p = 0; p < n && picks.length < 5; p += Math.max(1, Math.floor(n / 6))) if (probe.getParagraphLength(0, p) > 10) picks.push(p);
  for (const p of picks) {
    const doc = new m.HwpDocument(bytes);
    doc.splitParagraph(0, p, doc.getParagraphLength(0, p));
    const w = Math.round((40 * 7200) / 25.4);
    const r = JSON.parse(doc.insertPictureEx(JSON.stringify({ sectionIdx: 0, paraIdx: p + 1, charOffset: 0, cellPath: '', width: w, height: w, naturalWidthPx: 1, naturalHeightPx: 1, extension: 'png', description: '' }), PNG));
    if (r.ok) doc.setPictureProperties(0, r.paraIdx, r.controlIdx, JSON.stringify({ treatAsChar: true }));
    const p1 = problems(doc);
    report('본문 그림', { p }, r.ok && !worse(p1), `넘침 ${p1.over} 겹침 ${p1.overlap}`);
  }
}
console.log(`${path.basename(file)}: 처음 넘침 ${base.over} 겹침 ${base.overlap} | 실패 ${fails}${fixed ? `, 바로잡힘 ${fixed}` : ''}`);
process.exit(fails ? 1 : 0);
