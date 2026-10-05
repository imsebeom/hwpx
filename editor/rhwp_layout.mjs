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
 * 셀 안의 표도 같은 규칙에 걸리므로 경로 API(…ByPath)로 함께 잰다(2026-10-05 문항카드: 문항 전체가 큰 표 한 칸에
 * 들어 있고 안쪽 글상자와 그래프 상자 높이가 6082 로 낡아 글 줄이 겹치고 그래프가 잘렸다). 글상자 안의 표는 건드리지 않는다.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { readZip, writeZip, stripDummyLinesegs } from './hwpx-zip.mjs';
import { docFontMetrics, registerInto } from './font-metrics.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
let engineMod = null;

/** 엔진 모듈(rhwp.js 의 내보내기 전부). 서버가 글꼴 폭 표를 고를 때도 같은 것을 쓴다 */
export async function engineModule() {
  if (engineMod) return engineMod;
  // setup.mjs 가 번들과 같은 WASM 을 둔다. 에디터를 빌드하지 않은 PC 에서 빌드 마지막 보정을 할 때는
  // scripts/rhwp_convert.py 가 받아 둔 npm @rhwp/core 폴더를 RHWP_ENGINE 으로 넘긴다.
  const dir = process.env.RHWP_ENGINE || path.join(HERE, 'studio-dist', 'node');
  const m = await import(pathToFileURL(path.join(dir, 'rhwp.js')).href);
  m.initSync({ module: fs.readFileSync(path.join(dir, 'rhwp_bg.wasm')) });
  return (engineMod = m);
}

/**
 * section XML 의 표 나무. 본문 표 목록을 돌려주고, 표마다 칸 → 칸 문단 → 그 문단의 표(순서대로)를 단다.
 * 글상자처럼 칸 문단 안 다른 개체 속의 표는 경로를 만들 수 없어 inShape 로 표시한다.
 */
function tableTree(xml) {
  const body = [];
  const tables = [];   // 열린 표
  const cells = [];    // 열린 칸 { paras: [[표…]], para, pDepth }
  for (const m of xml.matchAll(/<hp:tbl\b[^>]*>|<\/hp:tbl>|<hp:tc\b[^>]*>|<\/hp:tc>|<hp:p\b[^>]*?(\/?)>|<\/hp:p>/g)) {
    const tag = m[0];
    const cell = cells[cells.length - 1];
    if (tag.startsWith('<hp:tbl')) {
      const node = {
        start: m.index,
        rows: Number(/rowCnt="(\d+)"/.exec(tag)?.[1]),
        cols: Number(/colCnt="(\d+)"/.exec(tag)?.[1]),
        cells: [],
        inShape: !!cell && cell.pDepth > 1,
      };
      if (!cell) body.push(node);
      else if (cell.para >= 0) (cell.paras[cell.para] ??= []).push(node);
      tables.push(node);
    } else if (tag === '</hp:tbl>') {
      tables.pop();
    } else if (tag.startsWith('<hp:tc')) {
      const c = { paras: [], para: -1, pDepth: 0 };
      tables[tables.length - 1]?.cells.push(c);
      cells.push(c);
    } else if (tag === '</hp:tc>') {
      cells.pop();
    } else if (tag.startsWith('<hp:p') && cell) {
      if (m[1] === '/') { if (cell.pDepth === 0) cell.para++; continue; }
      if (cell.pDepth === 0) cell.para++;
      cell.pDepth++;
    } else if (tag === '</hp:p>' && cell) {
      cell.pDepth--;
    }
  }
  return body;
}

/**
 * 한 칸(글상자 포함 subList) 안에 줄 배치가 있는 문단과 없는 문단이 섞여 있으면 그 칸의 줄 배치를 안쪽 칸까지 모두 걷는다.
 * 에디터가 저장한 판은 표를 담은 문단에만 그때의 줄 위치를 남기는데, 내용이 바뀐 뒤 rhwp 가 그 낡은 위치를 믿어
 * 칸 내용이 아래로 밀리고 끝이 잘렸다(2026-10-05 문항카드). 한글이 저장한 문서는 섞이지 않아 그대로 둔다.
 */
function stripMixedCellLinesegs(xml) {
  const frames = [];   // 열린 subList { start, has, lacks }
  const paras = [];    // 열린 문단 { frame, has }
  const spans = [];
  for (const m of xml.matchAll(/<hp:subList\b[^>]*>|<\/hp:subList>|<hp:p\b[^>]*?(\/?)>|<\/hp:p>|<hp:linesegarray>/g)) {
    const tag = m[0];
    if (tag.startsWith('<hp:subList')) frames.push({ start: m.index, has: 0, lacks: 0 });
    else if (tag === '</hp:subList>') {
      const f = frames.pop();
      if (f && f.has && f.lacks) spans.push([f.start, m.index]);
    } else if (tag.startsWith('<hp:p')) {
      const frame = frames[frames.length - 1] ?? null;
      if (m[1] === '/') { if (frame) frame.lacks++; continue; }
      paras.push({ frame, has: false });
    } else if (tag === '</hp:p>') {
      const p = paras.pop();
      if (p?.frame) p.has ? p.frame.has++ : p.frame.lacks++;
    } else {
      const p = paras[paras.length - 1];
      if (p) p.has = true;
    }
  }
  if (!spans.length) return { xml, cells: 0 };
  const inSpan = (i) => spans.some(([a, b]) => a <= i && i < b);
  let removed = 0;
  const out = xml.replace(/<hp:linesegarray>[\s\S]*?<\/hp:linesegarray>/g, (s, i) => (inSpan(i) ? (removed++, '') : s));
  return { xml: out, cells: spans.length, removed };
}

/** 모든 깊이의 표를 문서 순서로. */
function allTables(body) {
  const out = [];
  const walk = (t) => { out.push(t); for (const c of t.cells) for (const ts of c.paras) for (const n of ts ?? []) walk(n); };
  body.forEach(walk);
  return out.sort((a, b) => a.start - b.start);
}

/** 표마다 (node.start → 높이) 를 적는다(글자처럼 취급하는 표만, 값이 없으면 그대로). 바꾼 수도 돌려준다. */
function setHeights(xml, heightOf) {
  const pos = allTables(tableTree(xml)).map((t) => t.start);
  let res = xml, changed = 0;
  for (let i = pos.length - 1; i >= 0; i--) {
    const h = heightOf(pos[i], i);
    if (h == null) continue;
    const start = pos[i];
    const posAt = res.indexOf('<hp:pos ', start);
    if (posAt < 0 || !/^<hp:pos [^>]*treatAsChar="1"/.test(res.slice(posAt, posAt + 300))) continue;
    const szAt = res.indexOf('<hp:sz ', start);
    const szEnd = res.indexOf('/>', szAt);
    res = res.slice(0, szAt) + res.slice(szAt, szEnd).replace(/height="\d+"/, `height="${h}"`) + res.slice(szEnd);
    changed++;
  }
  return { xml: res, changed };
}

/** 반환: { buf, tables } — 고칠 표가 없으면 더미만 걷은 buf, tables 0. */
export async function rhwpLayout(input) {
  const mod = await engineModule();
  const Doc = mod.HwpDocument;
  // 엔진에 폭 표가 없는 글꼴은 설치된 글꼴 파일에서 읽어 등록한다(브라우저 엔진과 같은 폭으로 재야 표 높이가 맞는다)
  registerInto(mod, docFontMetrics(input, mod).metrics);
  const entries = readZip(stripDummyLinesegs(input).buf);
  const secs = entries.filter((e) => /^Contents\/section\d+\.xml$/.test(e.name))
    .sort((a, b) => Number(a.name.match(/\d+/)[0]) - Number(b.name.match(/\d+/)[0]));
  const orig = secs.map((e) => stripMixedCellLinesegs(e.data.toString('utf8')).xml);
  const trees = orig.map((x) => tableTree(x));

  // ① 높이 0 으로 열어 잰다
  let zeroed = 0;
  secs.forEach((e, s) => {
    const r = setHeights(orig[s], () => 0);
    zeroed += r.changed;
    e.data = Buffer.from(r.xml, 'utf8');
  });
  if (!zeroed) { secs.forEach((e, s) => { e.data = Buffer.from(orig[s], 'utf8'); }); return { buf: writeZip(entries), tables: 0 }; }
  const doc = new Doc(new Uint8Array(writeZip(entries)));
  const secCount = doc.getSectionCount();
  const ctrls = JSON.parse(doc.getControls()).filter((c) => c.ctrlId === 'tbl' && c.list < secCount);
  // 행마다 rowSpan 1 칸의 가장 큰 높이를 더한다. 쪽을 넘는 행은 조각을 따로 센다
  const heightOfBoxes = (boxes) => {
    const rows = new Map();
    for (const b of boxes) {
      if (b.rowSpan !== 1) continue;
      const k = `${b.row}@${b.pageIndex}`;
      rows.set(k, Math.max(rows.get(k) ?? 0, b.h));
    }
    return Math.round([...rows.values()].reduce((a, b) => a + b, 0) * 75);   // px → HWPUNIT(96dpi)
  };
  const heights = orig.map(() => new Map());   // 구역마다 node.start → 높이
  const bodyCount = trees.map(() => 0);
  // 칸 안의 표: XML 순서로 경로를 만든다. 문단 안 컨트롤 번호는 엔진이 표로 여는 번호를 차례로 맞춘다
  const nested = (s, para, prefix, node) => {
    node.cells.forEach((cell, ci) => {
      cell.paras.forEach((ts, pi) => {
        if (!ts?.length) return;
        const here = prefix.slice(0, -1).concat({ ...prefix[prefix.length - 1], cellIndex: ci, cellParaIndex: pi });
        const tableCtrls = [];
        for (let k = 0; k < 32 && tableCtrls.length < ts.length; k++) {
          try { doc.getTableDimensionsByPath(s, para, JSON.stringify([...here, { controlIndex: k, cellIndex: 0, cellParaIndex: 0 }])); tableCtrls.push(k); } catch { /* 표가 아니다 */ }
        }
        ts.forEach((t, k) => {
          if (t.inShape || tableCtrls[k] == null) return;
          const pathJson = JSON.stringify([...here, { controlIndex: tableCtrls[k], cellIndex: 0, cellParaIndex: 0 }]);
          try {
            const dim = JSON.parse(doc.getTableDimensionsByPath(s, para, pathJson));
            if (dim.rowCount !== t.rows || dim.colCount !== t.cols) return;   // 짝이 틀렸다 — 그대로 둔다
            heights[s].set(t.start, heightOfBoxes(JSON.parse(doc.getTableCellBboxesByPath(s, para, pathJson))));
          } catch { return; }
          nested(s, para, [...here, { controlIndex: tableCtrls[k], cellIndex: 0, cellParaIndex: 0 }], t);
        });
      });
    });
  };
  const pageOf = (s, p) => { try { return JSON.parse(doc.getPageOfPosition(s, p)).page; } catch { return null; } };
  for (const c of ctrls) {
    let boxes;
    // 엔진은 본문 표를 (문단 번호, 컨트롤 번호)로만 찾아 번호가 같은 다른 표 속의 표까지 집는다(2쪽 그래프 상자가 3쪽 표 높이에
    // 더해져 표가 쪽 밖으로 나갔다, 2026-10-05). 표가 놓일 수 있는 쪽 — 이 문단의 쪽부터 다음 문단의 쪽까지 — 만 받는다.
    const first = pageOf(c.list, c.para);
    const last = pageOf(c.list, c.para + 1);
    try { boxes = JSON.parse(doc.getTableCellBboxes(c.list, c.para, c.controlIndex, first ?? undefined)); } catch { continue; }   // 본문 표가 아니다
    boxes = boxes.filter((b) => (first == null || b.pageIndex >= first) && (last == null || b.pageIndex <= last));
    const node = trees[c.list][bodyCount[c.list]++];
    if (!node) continue;
    heights[c.list].set(node.start, heightOfBoxes(boxes));
    nested(c.list, c.para, [{ controlIndex: c.controlIndex, cellIndex: 0, cellParaIndex: 0 }], node);
  }
  doc.free?.();
  bodyCount.forEach((n, s) => { if (n !== trees[s].length) throw new Error(`section${s} 표 수가 맞지 않는다(${n}/${trees[s].length})`); });

  // ② 잰 높이를 적는다
  let tables = 0;
  secs.forEach((e, s) => {
    const r = setHeights(orig[s], (start) => heights[s].get(start));
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
