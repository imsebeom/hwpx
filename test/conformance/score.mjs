// rhwp 조판이 한/글과 얼마나 같은가를 잰다(일치율 채점기).
//
// 정답: oracle_driver.py 가 한/글로 다시 저장한 out/oracle/<id>.hwpx 의 줄 배치(<hp:lineseg textpos, vertpos>).
// 비교 대상: 같은 정답본에서 줄 배치만 지운 사본을 rhwp 로 열어 엔진이 계산한 줄 시작(getLineStarts).
//   rhwp 는 줄 배치가 적혀 있으면 그대로 믿으므로(2026-10-17 확인) 반드시 지우고 넣는다.
//   내용과 구조가 정답과 같으니 차이는 조판 차이다. hwp 원본도 한/글이 저장한 HWPX 정답본을 거친다.
// 글꼴: 에디터 서버처럼 엔진에 폭 표가 없는 글꼴은 설치된 글꼴 파일에서 읽어 등록한다(NO_FONT_FILES=1 이면 안 함).
//
// 지표
//   ① 본문 문단 줄바꿈 일치율(전체, 여러 줄 문단만) ② 칸 문단 줄바꿈 일치율(칸 목록이 1:1 로 대응하는 문서만)
//   ③ 문서 쪽수 일치율 ④ 본문 문단이 같은 쪽에 놓인 비율(한/글 쪽은 vertpos 가 되감기는 곳으로 매기며,
//      그렇게 센 쪽수가 한/글 PageCount 와 같은 문서만 쓴다)
//
//   node score.mjs [출력폴더=out/score]   → scoreboard.json, mismatches.jsonl, 요약 출력
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ED = 'C:/Users/hccga/.claude/skills/hwpx/editor/';
const m = await import(pathToFileURL(ED + 'studio-dist/node/rhwp.js').href);
m.initSync({ module: fs.readFileSync(ED + 'studio-dist/node/rhwp_bg.wasm') });
const { readZip, writeZip } = await import(pathToFileURL(ED + 'hwpx-zip.mjs').href);
const { docFontMetrics, registerInto } = await import(pathToFileURL(ED + 'font-metrics.mjs').href);

const OUT = path.join(HERE, 'out');
const DST = process.argv[2] || path.join(OUT, 'score');
fs.mkdirSync(DST, { recursive: true });
const SEG = /<hp:linesegarray>[\s\S]*?<\/hp:linesegarray>/g;

// 엔진에 폭 표가 있는 글꼴(font_cover.py 결과). 없으면 분류에서 「알 수 없음」
const metricFaces = new Map();
const tsv = path.join(HERE, '..', 'linebreak', 'results', 'corpus_faces_metric.tsv');
if (fs.existsSync(tsv)) {
  // 줄마다 「있음(1/0)\t글꼴 이름」, 머리줄 없음
  for (const line of fs.readFileSync(tsv, 'utf8').split(/\r?\n/)) {
    const [has, face] = line.split('\t');
    if (face) metricFaces.set(face, has === '1' ? '엔진표' : '엔진표없음');
  }
}

const sections = (buf) =>
  readZip(buf, (n) => /^Contents\/section\d+\.xml$/.test(n)).sort((a, b) => a.name.localeCompare(b.name, 'en', { numeric: true }));

/** header.xml: charPr id → { face(한글), height } */
function charInfo(buf) {
  const h = readZip(buf, (n) => n === 'Contents/header.xml')[0]?.data.toString('utf8') || '';
  const faces = {};
  const hangul = h.match(/<hh:fontface\b[^>]*lang="HANGUL"[^>]*>([\s\S]*?)<\/hh:fontface>/);
  if (hangul) for (const f of hangul[1].matchAll(/<hh:font\b[^>]*\bid="(\d+)"[^>]*\bface="([^"]*)"/g)) faces[f[1]] = f[2];
  const out = {};
  for (const c of h.matchAll(/<hh:charPr\b([^>]*)>([\s\S]*?)<\/hh:charPr>/g)) {
    const id = c[1].match(/\bid="(\d+)"/)?.[1];
    const height = +(c[1].match(/\bheight="(\d+)"/)?.[1] || 0);
    const ref = c[2].match(/<hh:fontRef\b[^>]*\bhangul="(\d+)"/)?.[1];
    if (id != null) out[id] = { face: faces[ref] ?? '?', height };
  }
  return out;
}

/**
 * 정답본 XML 을 훑어 문단마다 { starts, vpos, text, tab, ctrl, charPr } 를 낸다.
 * 본문(최상위) 문단은 body 에, 부모가 칸인 subList 의 문단은 cells[목록 순번] 에 둔다. 글상자, 머리말 등의 문단은 버린다.
 */
function parseOracle(buf) {
  const body = [], cells = [];
  const TOK = /<(\/?)hp:([A-Za-z]+)\b([^>]*?)(\/?)>/g;
  for (const s of sections(buf)) {
    const xml = s.data.toString('utf8');
    const stack = []; // { name, rec?, list? }
    let inT = null, last = 0;
    for (const x of xml.matchAll(TOK)) {
      if (inT && x.index > last) inT.text += xml.slice(last, x.index);
      last = x.index + x[0].length;
      const close = x[1] === '/', name = x[2], attrs = x[3], self = x[4] === '/';
      const topP = () => [...stack].reverse().find((e) => e.name === 'p')?.rec;
      if (close) {
        if (name === 't') inT = null;
        // 짝이 맞는 요소까지 걷어 낸다(자기 닫힘이 아닌 것만 쌓았다)
        while (stack.length) { const e = stack.pop(); if (e.name === name) break; }
        continue;
      }
      if (name === 'p') {
        const sl = [...stack].reverse().find((e) => e.name === 'subList');
        const rec = { starts: [], vpos: [], text: '', tab: false, ctrl: false, charPr: null };
        if (!sl) body.push(rec);
        else if (sl.cell >= 0) cells[sl.cell].push(rec);
        if (!self) stack.push({ name, rec });
        continue;
      }
      if (name === 'subList') {
        const parent = stack.length ? stack[stack.length - 1].name : null;
        const e = { name, cell: -1 };
        if (parent === 'tc') { e.cell = cells.length; cells.push([]); }
        if (!self) stack.push(e);
        continue;
      }
      if (name === 'lineseg') {
        const rec = topP();
        if (rec) {
          rec.starts.push(+(attrs.match(/\btextpos="(\d+)"/)?.[1] || 0));
          rec.vpos.push(+(attrs.match(/\bvertpos="(-?\d+)"/)?.[1] || 0));
        }
        continue;
      }
      if (name === 'run') {
        const rec = topP();
        if (rec && rec.charPr == null) rec.charPr = attrs.match(/\bcharPrIDRef="(\d+)"/)?.[1] ?? null;
      } else if (name === 't') {
        if (!self) inT = topP() || null;
      } else if (name === 'tab') {
        const rec = topP(); if (rec) rec.tab = true;
      } else if (['ctrl', 'tbl', 'pic', 'equation', 'rect', 'line', 'ellipse', 'container', 'fieldBegin'].includes(name)) {
        const rec = topP(); if (rec) rec.ctrl = true;
      }
      if (!self) stack.push({ name });
    }
  }
  return { body, cells };
}

function strip(buf) {
  const es = readZip(buf);
  for (const e of es) if (/^Contents\/section\d+\.xml$/.test(e.name)) e.data = Buffer.from(e.data.toString('utf8').replace(SEG, ''), 'utf8');
  return writeZip(es);
}

/** 한/글 쪽: 본문 문단의 첫 줄 vertpos 가 앞 문단 마지막 줄보다 작아지면 새 쪽 */
function hanPages(body) {
  let page = 0, prev = -1;
  return body.map((r) => {
    if (!r.vpos.length) return page;
    if (prev >= 0 && r.vpos[0] < prev) page++;
    prev = r.vpos[r.vpos.length - 1];
    return page;
  });
}

const eq = (a, b) => a.length === b.length && a.every((v, i) => v === b[i]);
const oracleRecs = fs.readFileSync(path.join(OUT, 'oracle.jsonl'), 'utf8').split(/\r?\n/).filter(Boolean).map((l) => JSON.parse(l));
const index = JSON.parse(fs.readFileSync(path.join(OUT, 'index.json'), 'utf8'));
const docs = [];
const mism = [];
let registered = 0;

for (const o of oracleRecs.sort((a, b) => a.id.localeCompare(b.id))) {
  const file = path.join(OUT, 'oracle', o.id + '.hwpx');
  const d = { id: o.id, src: index[o.id], hanPages: o.pages ?? null };
  if (!o.saved || !fs.existsSync(file)) { d.skip = o.open === false ? '한글 열기 실패' : o.missing ? '원본 없음' : '정답본 없음'; docs.push(d); continue; }
  try {
    const buf = fs.readFileSync(file);
    const ora = parseOracle(buf);
    const chars = charInfo(buf);
    const input = strip(buf);
    if (!process.env.NO_FONT_FILES) registered += registerInto(m, docFontMetrics(input, m).metrics);
    const doc = new m.HwpDocument(input);
    const cm = JSON.parse(doc.getCursorModel());
    d.rhwpPages = doc.pageCount();

    const record = (where, li, pi, h, r) => {
      const k = h.starts.findIndex((v, i) => v !== r[i]);
      const first = k >= 0 ? k : Math.min(h.starts.length, r.length);
      const c = chars[h.charPr] || {};
      mism.push({
        id: o.id, where, list: li, para: pi, hanLines: h.starts.length, rhwpLines: r.length, firstLine: first,
        delta: first < h.starts.length && first < r.length ? r[first] - h.starts[first] : null,
        tab: h.tab, ctrl: h.ctrl, face: c.face ?? '?', height: c.height ?? 0,
        metric: metricFaces.get(c.face) ?? '?', text: h.text.slice(0, 60),
      });
    };

    // ① 본문
    const n = cm.root?.paraCount ?? 0;
    d.body = { han: ora.body.length, rhwp: n, compared: 0, same: 0, multi: 0, multiSame: 0 };
    if (n === ora.body.length) {
      for (let p = 0; p < n; p++) {
        const h = ora.body[p];
        if (!h.starts.length) continue;
        const r = JSON.parse(doc.getLineStarts(0, p));
        const ok = eq(h.starts, r);
        d.body.compared++; d.body.same += ok;
        if (h.starts.length > 1 || r.length > 1) { d.body.multi++; d.body.multiSame += ok; }
        if (!ok) record('본문', 0, p, h, r);
      }
    } else d.body.skip = '본문 문단 수 다름';

    // ② 칸
    const rl = (cm.lists || []).filter((l) => l.isCell);
    d.cell = { hanLists: ora.cells.length, rhwpLists: rl.length, compared: 0, same: 0, multi: 0, multiSame: 0 };
    const aligned = rl.length === ora.cells.length && rl.every((l, i) => l.paraCount === ora.cells[i].length);
    d.cell.unmeasured = 0;
    if (aligned) {
      rl.forEach((l, i) => {
        for (let k = 0; k < l.paraCount; k++) {
          const h = ora.cells[i][k];
          if (!h.starts.length) continue;
          // 표 안 표의 칸은 엔진이 줄 배치를 문단 모형에 두지 않아 getLineStarts 가 언제나 [] 다(270칸 중 269칸,
          // 모든 쪽을 그린 뒤에도 같음). 조판 차이가 아니라 잴 수 없는 것이므로 따로 센다.
          if (l.hostListId !== 0) { d.cell.unmeasured++; continue; }
          const r = JSON.parse(doc.getLineStarts(l.listId, k));
          const ok = eq(h.starts, r);
          d.cell.compared++; d.cell.same += ok;
          if (h.starts.length > 1 || r.length > 1) { d.cell.multi++; d.cell.multiSame += ok; }
          if (!ok) record('칸', l.listId, k, h, r);
        }
      });
    } else d.cell.skip = '칸 목록 대응 안 됨';

    // ④ 본문 문단의 쪽
    const hp = hanPages(ora.body);
    const hanCounted = hp.length ? hp[hp.length - 1] + 1 : 0;
    d.paraPage = { hanCounted, compared: 0, same: 0 };
    if (hanCounted === o.pages && n === ora.body.length) {
      let g = 0;
      for (let s = 0; s < 64 && g < n; s++) {
        let cnt;
        try { cnt = doc.getParagraphCount(s); } catch { break; }
        for (let p = 0; p < cnt && g < n; p++, g++) {
          let v;
          try { v = JSON.parse(doc.getPageOfPosition(s, p)).page; } catch { v = -1; }
          d.paraPage.compared++; d.paraPage.same += v === hp[g];
        }
      }
    } else d.paraPage.skip = `vertpos 로 센 쪽수(${hanCounted})가 한글 쪽수(${o.pages})와 다르거나 본문 문단 수 다름`;
    doc.free?.();
  } catch (e) {
    d.error = String(e).slice(0, 200);
  }
  docs.push(d);
}

// 합계
const sum = (f) => docs.reduce((a, d) => a + (f(d) || 0), 0);
const pct = (a, b) => (b ? Math.round((1000 * a) / b) / 10 : null);
const scored = docs.filter((d) => !d.skip && !d.error);
const summary = {
  문서: { 전체: docs.length, 채점: scored.length, 건너뜀: docs.length - scored.length - docs.filter((d) => d.error).length, 오류: docs.filter((d) => d.error).length },
  본문줄바꿈: { 비교: sum((d) => d.body?.compared), 같음: sum((d) => d.body?.same), 일치율: pct(sum((d) => d.body?.same), sum((d) => d.body?.compared)),
    여러줄비교: sum((d) => d.body?.multi), 여러줄같음: sum((d) => d.body?.multiSame), 여러줄일치율: pct(sum((d) => d.body?.multiSame), sum((d) => d.body?.multi)),
    대응안된문서: scored.filter((d) => d.body?.skip).length },
  칸줄바꿈: { 비교: sum((d) => d.cell?.compared), 같음: sum((d) => d.cell?.same), 일치율: pct(sum((d) => d.cell?.same), sum((d) => d.cell?.compared)),
    여러줄비교: sum((d) => d.cell?.multi), 여러줄같음: sum((d) => d.cell?.multiSame), 여러줄일치율: pct(sum((d) => d.cell?.multiSame), sum((d) => d.cell?.multi)),
    대응안된문서: scored.filter((d) => d.cell?.skip).length, 표안표칸측정불가: sum((d) => d.cell?.unmeasured) },
  쪽수: { 비교: scored.length, 같음: scored.filter((d) => d.rhwpPages === d.hanPages).length, 일치율: pct(scored.filter((d) => d.rhwpPages === d.hanPages).length, scored.length) },
  문단쪽: { 비교: sum((d) => d.paraPage?.compared), 같음: sum((d) => d.paraPage?.same), 일치율: pct(sum((d) => d.paraPage?.same), sum((d) => d.paraPage?.compared)),
    쓴문서: scored.filter((d) => d.paraPage && !d.paraPage.skip).length },
  글꼴파일등록: registered,
};
fs.writeFileSync(path.join(DST, 'scoreboard.json'), JSON.stringify({ summary, docs }, null, 1));
fs.writeFileSync(path.join(DST, 'mismatches.jsonl'), mism.map((x) => JSON.stringify(x)).join('\n') + '\n');
console.log(JSON.stringify(summary, null, 1));
