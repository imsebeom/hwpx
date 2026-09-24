// 동시 편집용 편집 목록 도구: 문서 글 모델, 두 모델의 차이를 편집 목록으로, 편집 목록끼리의 문단 번호 변환.
// 브라우저(앱), 서버(Node), 스튜디오 플러그인 공용. 편집 목록은 doc-tools 의 runTool 이 그대로 실행한다.
//
// 모델: { paras: ['글', …](구역 0 본문 문단), cells: { 'T1r0c1#0': '셀 문단 글' }, shape: '표 모양 서명', sections }
// 손 편집은 문단 글과 셀 문단 글의 차이로 잡는다. 서식만 바뀐 편집, 표 모양이 바뀐 편집, 구역이 여럿인 문서는
// 글 차이로 표현할 수 없어 { reset: true } 를 돌려준다(보낸 쪽 문서 전체로 모두를 맞춘다).
import { listTables } from './doc-tools.js';

const J = (s) => (typeof s === 'string' ? JSON.parse(s) : s);

export function modelOf(doc) {
  const sections = doc.getSectionCount();
  const n = doc.getParagraphCount(0);
  const paras = [];
  for (let p = 0; p < n; p++) {
    const len = doc.getParagraphLength(0, p);
    paras.push(len ? doc.getTextRange(0, p, 0, len) : '');
  }
  const cells = {};
  const shape = [];
  for (const t of listTables(doc)) {
    const dim = J(doc.getTableDimensions(t.section, t.para, t.ctrl));
    const spans = [];
    for (let c = 0; c < dim.cellCount; c++) {
      const info = J(doc.getCellInfo(t.section, t.para, t.ctrl, c));
      spans.push(`${info.row}.${info.col}.${info.rowSpan}.${info.colSpan}`);
      const k = doc.getCellParagraphCount(t.section, t.para, t.ctrl, c);
      for (let i = 0; i < k; i++) {
        const l = doc.getCellParagraphLength(t.section, t.para, t.ctrl, c, i);
        cells[`${t.id}r${info.row}c${info.col}#${i}`] = l ? doc.getTextInCell(t.section, t.para, t.ctrl, c, i, 0, l) : '';
      }
      shape.push(`${t.id}r${info.row}c${info.col}:${k}`);
    }
    shape.push(`${t.id}@${t.section}.${t.para}:${spans.join(',')}`);
  }
  return { paras, cells, shape: shape.join('|'), sections };
}

/** 앞뒤 공통 부분을 빼고 바뀐 가운데만 돌려준다. 바뀐 게 없으면 null. */
function splice(a, b) {
  if (a === b) return null;
  let s = 0;
  while (s < a.length && s < b.length && a[s] === b[s]) s++;
  let e = 0;
  while (e < a.length - s && e < b.length - s && a[a.length - 1 - e] === b[b.length - 1 - e]) e++;
  return { offset: s, len: a.length - s - e, text: b.slice(s, b.length - e) };
}

/**
 * 표 문단(표 컨트롤이 든 문단)은 옮기거나 지우면 표 번호가 바뀌므로, 표 문단 위치가 달라지면 reset 으로 본다.
 * 반환: { ops } 또는 { reset: true, why }
 */
export function diffModels(a, b) {
  if (a.sections !== 1 || b.sections !== 1) return { reset: true, why: '구역이 여럿인 문서' };
  if (a.shape.replace(/@\d+\.\d+/g, '') !== b.shape.replace(/@\d+\.\d+/g, '')) return { reset: true, why: '표 모양이 바뀜' };
  const ops = [];
  // 문단: 앞뒤 공통 문단을 빼고, 가운데 구간을 문단 단위로 맞춘다.
  const A = a.paras;
  const B = b.paras;
  let s = 0;
  while (s < A.length && s < B.length && A[s] === B[s]) s++;
  let e = 0;
  while (e < A.length - s && e < B.length - s && A[A.length - 1 - e] === B[B.length - 1 - e]) e++;
  const oldMid = A.slice(s, A.length - e);
  const newMid = B.slice(s, B.length - e);
  if (oldMid.length || newMid.length) {
    // 문단 수가 같으면 제자리 고침. 다르면 겹치는 만큼 고치고 남는 것을 넣거나 지운다(Enter, 문단 합치기).
    const common = Math.min(oldMid.length, newMid.length);
    for (let i = 0; i < common; i++) {
      const sp = splice(oldMid[i], newMid[i]);
      if (sp) ops.push({ name: 'splice_paragraph', args: { para: s + i, ...sp } });
    }
    if (newMid.length > oldMid.length) {
      ops.push({ name: 'insert_paragraphs', args: { after_para: s + common - 1, texts: newMid.slice(common) } });
    } else if (oldMid.length > newMid.length) {
      if (s + common === 0) return { reset: true, why: '첫 문단을 지움' };
      ops.push({ name: 'delete_paragraphs', args: { from_para: s + common, to_para: s + oldMid.length - 1 } });
    }
    if (ops.some((o) => o.name === 'insert_paragraphs' && o.args.after_para < 0)) return { reset: true, why: '맨 앞에 문단을 넣음' };
  }
  // 표 문단 위치가 바뀌었는데 위 문단 편집으로 설명되지 않으면 reset
  const tableParas = (m) => [...m.shape.matchAll(/(T\d+)@0\.(\d+)/g)].map((x) => [x[1], Number(x[2])]);
  const shifted = shiftOf(ops);
  for (const [[id, pa], [, pb]] of zip(tableParas(a), tableParas(b))) {
    if (shifted(pa) !== pb) return { reset: true, why: `${id} 위치가 바뀜` };
  }
  // 셀: 셀 문단마다 글 차이
  for (const key of Object.keys(b.cells)) {
    const sp = splice(a.cells[key] ?? '', b.cells[key]);
    if (!sp) continue;
    const [, table, row, col, i] = key.match(/^(T\d+)r(\d+)c(\d+)#(\d+)$/);
    ops.push({ name: 'splice_cell', args: { table, row: Number(row), col: Number(col), cell_para: Number(i), ...sp } });
  }
  return { ops };
}

const zip = (x, y) => x.map((v, i) => [v, y[i] ?? v]);

/**
 * 편집 목록이 문단 번호를 어떻게 옮기는지. 반환: (옛 번호, 삽입 지점인가) → 새 번호(지워지면 null).
 * tieAfter: 같은 문단 뒤에 둘 다 넣을 때(삽입 지점이 같을 때) 이 편집 목록의 삽입 뒤로 보낸다.
 * 서버 순서가 앞선 편집에 대해 변환할 때 true 여야 모든 쪽이 같은 순서로 수렴한다.
 */
export function shiftOf(ops, tieAfter = false) {
  const steps = [];
  const after = (at, n) => (p, ins) => (p > at || (ins && tieAfter && p === at) ? p + n : p);
  for (const o of ops) {
    const a = o.args;
    if (o.name === 'insert_paragraphs') steps.push(after(a.after_para, a.texts.length));
    else if (o.name === 'replace_paragraph' && String(a.text).includes('\n')) steps.push(after(a.para, String(a.text).split('\n').length - 1));
    else if (o.name === 'delete_paragraphs') steps.push((p) => (p < a.from_para ? p : p > a.to_para ? p - (a.to_para - a.from_para + 1) : null));
    else if (o.name === 'create_table') steps.push(after(a.after_para, 1));
  }
  return (p, ins = false) => steps.reduce((v, f) => (v == null ? null : f(v, ins)), p);
}

const TABLE_CHANGING = new Set(['create_table', 'delete_table']);

/** 편집 목록이 건드리는 본문 문단 번호들(잠금 판정용). */
export function touchedParas(ops) {
  const out = new Set();
  for (const o of ops) {
    const a = o.args;
    for (const k of ['para', 'after_para']) if (Number.isInteger(a[k])) out.add(a[k]);
    if (Number.isInteger(a.from_para)) for (let p = a.from_para; p <= a.to_para; p++) out.add(p);
    const at = typeof a.at === 'string' ? a.at.match(/^p(\d+)(?:[-~]p?(\d+))?$/) : null;
    if (at) for (let p = Number(at[1]); p <= Number(at[2] ?? at[1]); p++) out.add(p);
  }
  return [...out];
}

/** 편집 목록이 건드리는 셀(T1r2c1)들(잠금 판정용). */
export function touchedCells(ops) {
  return [...new Set(ops.filter((o) => o.args.table && Number.isInteger(o.args.row)).map((o) => `${o.args.table}r${o.args.row}c${o.args.col}`))];
}

/**
 * ops 를 against(이미 적용된 남의 편집) 뒤에 적용할 수 있게 문단 번호를 옮긴다.
 * againstIsEarlier: against 가 서버 순서에서 앞선 편집이면 true(서버, 그리고 남의 편집을 받은 쪽).
 * 내가 먼저 적용해 둔 편집 위에 서버 순서가 앞선 남의 편집을 얹을 때는 false.
 * 옮길 수 없으면(지워진 문단을 건드림, 표 번호가 바뀜) null.
 */
export function transformOps(ops, against, againstIsEarlier = true) {
  if (!against.length) return ops;
  if (against.some((o) => TABLE_CHANGING.has(o.name)) && ops.some((o) => o.args.table)) return null;
  const f = shiftOf(against, againstIsEarlier);
  const out = [];
  for (const o of ops) {
    const a = { ...o.args };
    for (const k of ['para', 'after_para']) {
      if (!Number.isInteger(a[k])) continue;
      const v = f(a[k], k === 'after_para');
      if (v == null) return null;
      a[k] = v;
    }
    if (Number.isInteger(a.from_para)) {
      const from = f(a.from_para);
      const to = f(a.to_para);
      if (from == null || to == null || to - from !== a.to_para - a.from_para) return null;
      a.from_para = from;
      a.to_para = to;
    }
    if (typeof a.at === 'string') {
      const m = a.at.match(/^p(\d+)(?:[-~]p?(\d+))?$/);
      if (m) {
        const from = f(Number(m[1]));
        const to = f(Number(m[2] ?? m[1]));
        if (from == null || to == null) return null;
        a.at = m[2] ? `p${from}-p${to}` : `p${from}`;
      }
    }
    out.push({ ...o, args: a });
  }
  return out;
}
