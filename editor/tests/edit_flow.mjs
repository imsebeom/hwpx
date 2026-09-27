// 편집 흐름 회귀 시험. 에디터 엔진(studio-dist/node)으로 문서를 열어, 본문 글자처럼 취급 표마다 칸 편집을 해 보고
// 표 높이가 따라가는지, 쪽 끝을 넘거나 표와 겹치는 글 줄이 생기는지, 되돌린 뒤 원래대로인지 본다.
//   node editor/tests/edit_flow.mjs <문서.hwpx> [--verbose]
// 시험 종류: ① 칸 끝에 두 줄 넣기/지우기(미룬 쪽 나누기) ② 칸 Enter 두 번/합치기 ③ 칸 글자 16pt ④ 칸 안 그림 넣기
//          ⑤ 본문 그림 문단 넣기(문서 전체에서 5곳) ⑥ 마지막 행 아래 행 추가/삭제 ⑦ 열 추가/삭제 ⑧ 칸 합치기/나누기
// 판정: 처음에 없던 넘침, 겹침이 생기면 실패. ②는 칸이 표 밖으로 삐져나오면 실패. 글자 없는 줄은 넘침으로 세지 않는다
// (쪽 끝 빈 문단은 엔진이 높이 0으로 흡수한다).
// ①⑥은 되돌린 뒤 표 높이가 처음(①은 편집 기준값도 허용)과 1px 안이어야 한다(엔진 패치 tac-sync-offset 뒤로, 내용이 그대로면 높이도 그대로다).
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
    for (const r of JSON.parse(doc.getPageTextLayout(pg)).runs.filter((r) => !r.cellPath && r.paraIdx != null && r.w >= 1 && r.text?.trim())) {
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
// 칸 상자가 표 상자 아래로 삐져나온 길이(px). 표가 칸 내용을 따라가지 못하면 양수
function spill(doc, t) {
  for (let pg = 0; pg < doc.pageCount(); pg++) {
    let b;
    try { b = JSON.parse(doc.getTableBBoxAtPage(0, t.p, t.c, pg)); } catch { continue; }
    if (!b?.height) continue;
    const cells = JSON.parse(doc.getTableCellBboxes(0, t.p, t.c)).filter((c) => c.pageIndex === pg);
    return Math.max(0, ...cells.map((c) => c.y + c.h - (b.y + b.height)));
  }
  return 0;
}

const base = problems(new m.HwpDocument(bytes));
let fails = 0;
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
    // 편집 기준값: 같은 자리에 글 하나 넣고 지운 높이. 처음 그린 높이가 한글과 다른 표는 편집하면 기준값으로 간다
    // (d02 p5: 처음 106.9, 한글 98.0, 편집 뒤 98.0). 내용이 그대로면 둘 중 하나와 같아야 한다
    const noop = new m.HwpDocument(bytes);
    noop.insertTextInCell(0, t.p, t.c, 0, 0, len, 'x'); noop.deleteTextInCell(0, t.p, t.c, 0, 0, len, 1);
    const hn = height(noop, t);
    const back = Math.abs(h2 - h0) <= 1 || Math.abs(h2 - hn) <= 1;
    report('넣기/지우기', t, !worse(p1) && !worse(p2) && h1 > Math.min(h0, hn) - 0.5 && back,
      `높이 ${h0.toFixed(1)} → ${h1.toFixed(1)} → ${h2.toFixed(1)}${back ? '' : `(안 돌아옴, 편집 기준값 ${hn.toFixed(1)})`} 넘침 ${p1.over}/${p2.over} 겹침 ${p1.overlap}/${p2.overlap}`);
  }
  // ② Enter/합치기
  {
    const doc = new m.HwpDocument(bytes);
    const h0 = height(doc, t);
    const len = doc.getCellParagraphLength(0, t.p, t.c, 0, 0);
    doc.splitParagraphInCell(0, t.p, t.c, 0, 0, len);
    doc.splitParagraphInCell(0, t.p, t.c, 0, 1, 0);
    const h1 = height(doc, t), p1 = problems(doc), s1 = spill(doc, t);
    doc.mergeParagraphInCell(0, t.p, t.c, 0, 2);
    doc.mergeParagraphInCell(0, t.p, t.c, 0, 1);
    const h2 = height(doc, t), p2 = problems(doc);
    // 칸에 남는 자리가 있으면 표는 그대로다 — 칸이 표 밖으로 삐져나올 때만 실패
    report('Enter/합치기', t, !worse(p1) && !worse(p2) && h1 >= h0 - 0.5 && s1 <= 1, `높이 ${h0.toFixed(1)} → ${h1.toFixed(1)} → ${h2.toFixed(1)} 삐짐 ${s1.toFixed(1)} 넘침 ${p1.over}/${p2.over}`);
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
  // ⑥ 마지막 행 아래에 행 추가 뒤 지우기
  {
    const doc = new m.HwpDocument(bytes);
    const h0 = height(doc, t);
    const rows = JSON.parse(doc.getTableDimensions(0, t.p, t.c)).rowCount;
    const r = JSON.parse(doc.insertTableRow(0, t.p, t.c, rows - 1, true));
    const h1 = height(doc, t), p1 = problems(doc), s1 = spill(doc, t);
    doc.deleteTableRow(0, t.p, t.c, rows);
    const h2 = height(doc, t), p2 = problems(doc);
    const back = Math.abs(h2 - h0) <= 1;
    report('행 추가/삭제', t, r.ok && !worse(p1) && !worse(p2) && h1 > h0 + 1 && s1 <= 1 && back,
      `높이 ${h0.toFixed(1)} → ${h1.toFixed(1)} → ${h2.toFixed(1)}${back ? '' : '(안 돌아옴)'} 삐짐 ${s1.toFixed(1)} 넘침 ${p1.over}/${p2.over} 겹침 ${p1.overlap}/${p2.overlap}`);
  }
  // ⑦ 마지막 열 오른쪽에 열 추가 뒤 지우기 — 칸이 좁아져 줄이 늘어도 표가 따라가는지
  {
    const doc = new m.HwpDocument(bytes);
    const cols = JSON.parse(doc.getTableDimensions(0, t.p, t.c)).colCount;
    const r = JSON.parse(doc.insertTableColumn(0, t.p, t.c, cols - 1, true));
    const p1 = problems(doc), s1 = spill(doc, t);
    doc.deleteTableColumn(0, t.p, t.c, cols);
    const p2 = problems(doc), s2 = spill(doc, t);
    report('열 추가/삭제', t, r.ok && !worse(p1) && !worse(p2) && s1 <= 1 && s2 <= 1,
      `삐짐 ${s1.toFixed(1)}/${s2.toFixed(1)} 넘침 ${p1.over}/${p2.over} 겹침 ${p1.overlap}/${p2.overlap}`);
  }
  // ⑧ 첫 두 행의 첫 칸 합치기 뒤 나누기(두 행 이상)
  {
    const doc = new m.HwpDocument(bytes);
    const d = JSON.parse(doc.getTableDimensions(0, t.p, t.c));
    if (d.rowCount >= 2) {
      let r;
      try { r = JSON.parse(doc.mergeTableCells(0, t.p, t.c, 0, 0, 1, 0)); } catch { r = { ok: false }; }
      const p1 = problems(doc), s1 = spill(doc, t);
      const r2 = r.ok ? JSON.parse(doc.splitTableCell(0, t.p, t.c, 0, 0)) : { ok: false };
      const p2 = problems(doc), s2 = spill(doc, t);
      // 합칠 수 없는 모양(이미 합친 칸 등)은 엔진이 거절한다 — 그때는 넘어간다
      if (r.ok) report('칸 합치기/나누기', t, r2.ok && !worse(p1) && !worse(p2) && s1 <= 1 && s2 <= 1,
        `삐짐 ${s1.toFixed(1)}/${s2.toFixed(1)} 넘침 ${p1.over}/${p2.over} 겹침 ${p1.overlap}/${p2.overlap}`);
    }
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
console.log(`${path.basename(file)}: 처음 넘침 ${base.over} 겹침 ${base.overlap} | 실패 ${fails}`);
process.exit(fails ? 1 : 0);
