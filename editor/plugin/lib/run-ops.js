// @ts-nocheck
/**
 * 편집 작업 한 건(op)을 문서에 적용하는 공용 부분 — 에디터 플러그인(claude-plugin.ts)과 화면 없는 실행기(editor/apply_ops.mjs)가
 * 함께 쓴다. { tool } 은 doc-tools.js 도구와 이 파일의 추가 도구, { doc } 은 WASM HwpDocument 메서드다.
 * HwpCtrl({ m }, { run })과 그림({ image })은 화면이 있는 에디터에서만 된다(claude-plugin.ts).
 */
import { clean, listTables, outline, resolveTarget, runTool } from './doc-tools.js';

function parseMaybe(value) {
  if (typeof value !== 'string') return value;
  const s = value.trim();
  if (!(s.startsWith('{') || s.startsWith('['))) return value;
  try {
    return JSON.parse(s);
  } catch {
    return value;
  }
}

/** 이 플러그인에서 더한 편집 도구(doc-tools.js 는 형제 프로젝트에서 고치지 않고 가져온다). */
const EXTRA_TOOLS = [
  {
    name: 'clone_table',
    description: '문서에 이미 있는 표(그림 상자, 예시 프롬프트 상자 등)를 본보기로 복제해 after_para 문단 뒤에 넣고 칸 글만 바꾼다. 테두리, 칸 크기, 글자 모양이 본보기와 같다. rows 는 행마다 열 글 배열이고 null 인 칸은 본보기 글을 그대로 둔다. 칸 안 그림도 복제되니 바꾸려면 image 명령을 쓴다.',
    parameters: { type: 'object', properties: { model: { type: 'string', description: '본보기 표 T 번호' }, after_para: { type: 'integer' }, rows: { type: 'array', items: { type: 'array', items: { type: ['string', 'null'] } } } }, required: ['model', 'after_para'] },
  },
  {
    name: 'delete_cell_paragraphs',
    description: '표 칸 안의 문단을 지운다(delete_paragraphs 는 본문 문단만 지운다). cell 은 T3r1c0 이나 표 속 표 T15r0c0/T1r0c0. from_para~to_para(칸 문단 번호, 포함)를 지우거나, only_empty=true 로 글도 개체도 없는 빈 문단을 모두 지운다. 그림이나 표가 든 문단은 지우지 않는다. 번호를 모르면 둘 다 빼고 부르면 칸 문단 목록을 알려 준다. 칸에는 문단이 하나 이상 남는다.',
    parameters: { type: 'object', properties: { cell: { type: 'string' }, from_para: { type: 'integer' }, to_para: { type: 'integer' }, only_empty: { type: 'boolean' } }, required: ['cell'] },
  },
];

const EXTRA_RUN = {
  // 2026-10-02 가이드북 세션: create_table 로 만든 그림 상자는 글자가 12pt(문서의 그림 설명은 10pt)라 손으로 맞췄다
  clone_table(doc, a) {
    const t = listTables(doc).find((x) => x.id === a.model);
    if (!t) throw new Error(`${a.model} 표가 없습니다. outline 으로 T 번호를 확인하세요.`);
    const s = t.section;
    const n = doc.getParagraphCount(s);
    if (!(Number.isInteger(a.after_para) && a.after_para >= 0 && a.after_para < n)) throw new Error(`p${a.after_para} 는 범위 밖입니다(p0~p${n - 1}).`);
    const c = parseMaybe(doc.copyControl(s, t.para, '', t.ctrl ?? 0));
    if (!c?.ok) throw new Error(`${a.model} 복사 실패: ${JSON.stringify(c)}`);
    doc.insertParagraph(s, a.after_para + 1);
    const r = parseMaybe(doc.pasteControl(s, a.after_para + 1, 0));
    if (!r?.ok) throw new Error(`붙여넣기 실패: ${JSON.stringify(r)}`);
    const nt = listTables(doc).find((x) => x.section === s && x.para === r.paraIdx);
    let changed = 0;
    (a.rows || []).forEach((row, ri) => (row || []).forEach((text, ci) => {
      if (text == null) return;
      const { result } = runTool(doc, 'set_cell', { table: nt.id, row: ri, col: ci, text, keep_style: true });
      if (!result.ok) throw new Error(`${nt.id} r${ri}c${ci}: ${result.error}`);
      changed++;
    }));
    return { ok: true, table: nt.id, para: `p${r.paraIdx}`, cells: changed, note: `p${a.after_para} 뒤의 문단 번호가 +1, 그 뒤 표 번호가 +1 만큼 바뀌었습니다.` };
  },
  // 2026-10-17: 칸 안 문단을 지우는 이름 붙은 도구가 없어, 다른 세션이 그림 아래 빈 줄을 사용자에게 Backspace 로 지워 달라고 했다
  delete_cell_paragraphs(doc, a) {
    const x = resolveNested(doc, a.cell);
    const paras = nestedParas(doc, x).map((p) => ({ ...p, ctrl: hasCellControl(doc, x, p.i) }));
    const list = () => paras.map((p) => `${p.i}: ${p.ctrl ? '[개체] ' : ''}${p.text ? `「${p.text.slice(0, 30)}」` : '(빈 문단)'}`).join(', ');
    let targets;
    if (a.only_empty) {
      targets = paras.filter((p) => !p.len && !p.ctrl).map((p) => p.i);
      if (targets.length === paras.length) targets = targets.slice(1); // 칸에 문단 하나는 남긴다
    } else {
      if (a.from_para == null) throw new Error(`지울 문단을 from_para~to_para 나 only_empty 로 주세요. ${a.cell} 칸 문단: ${list()}`);
      const f = a.from_para, t = a.to_para ?? a.from_para;
      if (!(Number.isInteger(f) && Number.isInteger(t) && f >= 0 && f <= t && t < paras.length)) throw new Error(`칸 문단 범위가 틀렸습니다(0~${paras.length - 1}). ${a.cell} 칸 문단: ${list()}`);
      if (t - f + 1 === paras.length) throw new Error('칸의 문단을 모두 지울 수는 없습니다. 칸을 비우려면 set_cell 로 빈 글을 넣으세요.');
      const withCtrl = paras.slice(f, t + 1).find((p) => p.ctrl);
      if (withCtrl) throw new Error(`칸 문단 ${withCtrl.i} 에 그림이나 표가 있습니다. 그림은 image --replace, 표는 delete_table 로 다루세요. ${a.cell} 칸 문단: ${list()}`);
      targets = Array.from({ length: t - f + 1 }, (_, k) => f + k);
    }
    const removed = targets.map((i) => paras[i].text);
    const root = PJ(pathAt(x.path, 0));
    const len = (i) => doc.getCellParagraphLengthByPath(x.s, x.para, PJ(pathAt(x.path, i)));
    // 뒤에서부터 하나씩: 앞 문단 끝과 합쳐 지우고, 0번이면 다음 문단 처음까지 지운다
    for (const i of [...targets].sort((m, n) => n - m)) {
      if (i > 0) doc.deleteRangeInCellByPath(x.s, x.para, root, i - 1, len(i - 1), i, len(i));
      else doc.deleteRangeInCellByPath(x.s, x.para, root, 0, 0, 1, 0);
    }
    return { ok: true, at: a.cell, removed: removed.length, texts: removed, paragraphs: paras.length - removed.length };
  },
};

/** 칸 문단 i 에 그림이나 표가 있는가. */
function hasCellControl(doc, x, i) {
  const p = PJ(pathAt(x.path, i));
  for (let ci = 0; ci < 16; ci++) {
    try { doc.getCellPicturePropertiesByPath(x.s, x.para, p, ci); return true; } catch { /* 그림 아님 */ }
    try { doc.getTableDimensionsByPath(x.s, x.para, PJ([...pathAt(x.path, i), { controlIndex: ci, cellIndex: 0, cellParaIndex: 0 }])); return true; } catch { /* 표 아님 */ }
  }
  return false;
}

// ── 표 속 표 좌표 「T15r0c0/T1r0c0」(바깥 칸 안의 첫째 표 0행 0열, 단계는 / 로 더 이어진다) ──
// doc-tools.js 의 좌표는 본문 표 한 단계뿐이라 표 속 표의 글은 format_text, set_cell 이 닿지 않고 search_text 는
// 위치를 문단 번호로만, 문맥을 빈칸으로 돌려줬다(2026-10-02 가이드북 「교사 개발자 K의 노하우」 이름표).
const NESTED_RE = /^T\d+r\d+c\d+(?:\/T\d+r\d+c\d+)+$/i;
const PJ = (x) => JSON.stringify(x);

/** prefix(마지막 원소가 칸) 칸 안의 표들 — 칸 문단 순서, 그 안 컨트롤 순서. */
function innerTables(doc, s, para, prefix) {
  const out = [];
  const head = prefix.slice(0, -1);
  const last = prefix[prefix.length - 1];
  const n = doc.getCellParagraphCountByPath(s, para, PJ([...head, { ...last, cellParaIndex: 0 }]));
  for (let cp = 0; cp < n; cp++) {
    for (let ci = 0; ci < 16; ci++) {
      try {
        doc.getTableDimensionsByPath(s, para, PJ([...head, { ...last, cellParaIndex: cp }, { controlIndex: ci, cellIndex: 0, cellParaIndex: 0 }]));
        out.push({ cp, ci });
      } catch { /* 표가 아닌 컨트롤이거나 없음 */ }
    }
  }
  return out;
}

/** 표(경로의 마지막 원소가 그 표)의 칸 상자 [{cellIdx,row,col,rowSpan,colSpan}]. */
const cellBoxes = (doc, s, para, tablePath) => JSON.parse(doc.getTableCellBboxesByPath(s, para, PJ(tablePath)));

function resolveNested(doc, ref) {
  const parts = String(ref).replace(/\s+/g, '').split('/');
  const o = resolveTarget(doc, parts[0]);
  if (!o || o.cellIndex == null) throw new Error(`${parts[0]} 칸을 찾지 못했습니다.`);
  const s = o.sectionIndex, para = o.parentParaIndex;
  const path = [{ controlIndex: o.controlIndex, cellIndex: o.cellIndex, cellParaIndex: 0 }];
  let at = parts[0];
  for (const part of parts.slice(1)) {
    const [, k, r, c] = part.match(/^T(\d+)r(\d+)c(\d+)$/i).map(Number);
    const tables = innerTables(doc, s, para, path);
    const hit = tables[k - 1];
    if (!hit) throw new Error(`${at} 칸 안에 표가 ${tables.length}개라 T${k} 가 없습니다.`);
    path[path.length - 1].cellParaIndex = hit.cp;
    const tablePath = [...path, { controlIndex: hit.ci, cellIndex: 0, cellParaIndex: 0 }];
    const cell = cellBoxes(doc, s, para, tablePath).find((b) => r >= b.row && r < b.row + b.rowSpan && c >= b.col && c < b.col + b.colSpan);
    if (!cell) throw new Error(`${at}/T${k} 에 r${r}c${c} 칸이 없습니다.`);
    path.push({ controlIndex: hit.ci, cellIndex: cell.cellIdx, cellParaIndex: 0 });
    at += `/${part}`;
  }
  return { s, para, path };
}

const pathAt = (path, i) => [...path.slice(0, -1), { ...path[path.length - 1], cellParaIndex: i }];
function nestedParas(doc, x) {
  const n = doc.getCellParagraphCountByPath(x.s, x.para, PJ(pathAt(x.path, 0)));
  return Array.from({ length: n }, (_, i) => {
    const p = PJ(pathAt(x.path, i));
    const len = doc.getCellParagraphLengthByPath(x.s, x.para, p);
    return { i, p, len, text: len ? doc.getTextInCellByPath(x.s, x.para, p, 0, len) : '' };
  });
}

/** searchAllText 결과(cellPath 두 단계 이상)를 「T15r0c0/T1r0c0」로. */
function nestedRefOf(doc, h, tables) {
  const cp = h.cellPath;
  const outer = tables.find((t) => t.section === h.sec && t.para === h.para && t.ctrl === cp[0].controlIndex);
  if (!outer) return null;
  const ob = cellBoxes(doc, h.sec, h.para, [{ controlIndex: cp[0].controlIndex, cellIndex: 0, cellParaIndex: 0 }]).find((b) => b.cellIdx === cp[0].cellIndex);
  let ref = `${outer.id}r${ob?.row ?? '?'}c${ob?.col ?? '?'}`;
  for (let lv = 1; lv < cp.length; lv++) {
    const prefix = cp.slice(0, lv);
    const k = innerTables(doc, h.sec, h.para, prefix).findIndex((t) => t.cp === prefix[lv - 1].cellParaIndex && t.ci === cp[lv].controlIndex);
    const b = cellBoxes(doc, h.sec, h.para, [...prefix, { ...cp[lv], cellIndex: 0, cellParaIndex: 0 }]).find((x) => x.cellIdx === cp[lv].cellIndex);
    ref += `/T${k + 1}r${b?.row ?? '?'}c${b?.col ?? '?'}`;
  }
  return ref;
}

function nestedCharProps(a) {
  const props = {};
  for (const k of ['bold', 'italic', 'underline', 'strikethrough']) if (typeof a[k] === 'boolean') props[k] = a[k];
  if (a.size_pt != null) props.fontSize = Math.round(Number(a.size_pt) * 100);
  if (a.color) props.textColor = String(a.color).toLowerCase();
  return props;
}

/** 표 속 표 좌표가 든 도구 호출을 처리한다. 해당 없으면 null. */
function runNestedTool(doc, name, a) {
  // delete_table 은 표 속 표를 「T3r1c0/T1」(T3 의 r1c0 칸 안 첫째 표)로 받는다. 종전에는 본문 표만 지워, 다른 세션이 칸 안 표를
  // 지울 길을 못 찾고 멈췄다(2026-10-17 문항 4 자료 1). 표를 담던 문단은 빈 문단으로 남는다(한/글과 같음)
  if (name === 'delete_table' && String(a.table).includes('/')) {
    const ref = String(a.table).replace(/\s+/g, '');
    const m = ref.match(/^(.+)\/T(\d+)$/i);
    if (!m || !NESTED_RE.test(`${ref}r0c0`)) throw new Error(`표 속 표는 「T3r1c0/T1」처럼 바깥 칸 좌표 뒤에 /T번호로 적습니다: ${a.table}`);
    const x = resolveNested(doc, m[1]);
    const tables = innerTables(doc, x.s, x.para, x.path);
    const hit = tables[Number(m[2]) - 1];
    if (!hit) throw new Error(`${m[1]} 칸 안에 표가 ${tables.length}개라 T${m[2]} 가 없습니다.`);
    const dim = parseMaybe(doc.getTableDimensionsByPath(x.s, x.para, PJ([...pathAt(x.path, hit.cp), { controlIndex: hit.ci, cellIndex: 0, cellParaIndex: 0 }])));
    doc.deleteCellPictureControlByPath(x.s, x.para, PJ(pathAt(x.path, hit.cp)), hit.ci);
    return { ok: true, at: ref, removed: `${dim.rowCount}×${dim.colCount} 표`, cellPara: hit.cp, note: `${m[1]} 칸 문단 ${hit.cp} 는 빈 문단으로 남았습니다. 걷으려면 delete_cell_paragraphs {cell:"${m[1]}", only_empty:true}` };
  }
  // set_cell 은 table 에 바깥 칸까지 적고(「T15r0c0/T1」) row, col 로 안쪽 표 칸을 고른다
  if (name === 'set_cell' && String(a.table).includes('/')) {
    const x = resolveNested(doc, `${a.table}r${a.row}c${a.col}`);
    const paras = nestedParas(doc, x);
    const last = paras[paras.length - 1];
    if (paras.length > 1 || last.len) doc.deleteRangeInCellByPath(x.s, x.para, PJ(pathAt(x.path, 0)), 0, 0, last.i, last.len);
    const lines = clean(a.text).split('\n');
    lines.forEach((line, i) => {
      if (i > 0) {
        const prev = PJ(pathAt(x.path, i - 1));
        doc.splitParagraphInCellByPath(x.s, x.para, prev, doc.getCellParagraphLengthByPath(x.s, x.para, prev), undefined);
      }
      if (line) doc.insertTextInCellByPath(x.s, x.para, PJ(pathAt(x.path, i)), 0, line);
    });
    return { ok: true, at: `${a.table}r${a.row}c${a.col}`, paragraphs: lines.length };
  }
  if (name === 'format_text' && [].concat(a.at).some((t) => NESTED_RE.test(String(t).replace(/\s+/g, '')))) {
    const props = PJ(nestedCharProps(a));
    let n = 0;
    for (const at of [].concat(a.at)) {
      if (!NESTED_RE.test(String(at).replace(/\s+/g, ''))) {
        const { result } = runTool(doc, 'format_text', { ...a, at });
        if (!result.ok) throw new Error(result.error);
        n += result.ranges;
        continue;
      }
      const x = resolveNested(doc, at);
      for (const p of nestedParas(doc, x)) {
        if (!p.len) continue;
        if (!a.text) { doc.applyCharFormatInCellByPath(x.s, x.para, p.p, 0, p.len, props); n++; continue; }
        for (let k = p.text.indexOf(a.text); k >= 0; k = p.text.indexOf(a.text, k + a.text.length)) {
          doc.applyCharFormatInCellByPath(x.s, x.para, p.p, k, k + a.text.length, props);
          n++;
        }
      }
    }
    if (!n) throw new Error(a.text ? `「${a.text}」를 ${a.at} 에서 찾지 못했습니다.` : `${a.at} 에 글자가 없습니다.`);
    return { ok: true, ranges: n };
  }
  return null;
}

/** search_text 에서 표 속 표 결과의 위치와 문맥을 채운다(searchAllText 와 같은 순서, 앞 50개). */
function searchWithNested(doc, a) {
  const { result } = runTool(doc, 'search_text', a);
  if (!result.ok) throw new Error(result.error);
  const raw = JSON.parse(doc.searchAllText(a.query, !!a.case_sensitive, true)).slice(0, 50);
  const tables = listTables(doc);
  raw.forEach((h, i) => {
    if (!(h.cellPath?.length > 1) || !result.hits[i]) return;
    const ref = nestedRefOf(doc, h, tables);
    if (!ref) return;
    const p = PJ(h.cellPath);
    const len = doc.getCellParagraphLengthByPath(h.sec, h.para, p);
    const text = len ? doc.getTextInCellByPath(h.sec, h.para, p, 0, len) : '';
    result.hits[i] = { at: ref, context: text.slice(Math.max(0, h.charOffset - 20), h.charOffset + h.length + 20) };
  });
  return result;
}

/**
 * 칸 그림 바꾸기(image --replace): 칸의 그림을 모두 지우고 그림이 남긴 빈 문단을 걷는다. 글이 든 문단은 남긴다.
 * 종전에는 deleteCellPictureControlByPath 뒤 deleteRangeInCell 로 빈 문단을 손으로 합쳐야 했다(2026-10-02 가이드북 세션).
 */
function clearCellPictures(doc, s, ppi, ctrl, cell) {
  let removed = 0;
  const picParas = new Set();
  const path = (cp) => PJ([{ controlIndex: ctrl, cellIndex: cell, cellParaIndex: cp }]);
  const count = () => doc.getCellParagraphCount(s, ppi, ctrl, cell);
  const len = (cp) => doc.getCellParagraphLength(s, ppi, ctrl, cell, cp);
  for (let cp = count() - 1; cp >= 0; cp--) {
    for (let ci = 15; ci >= 0; ci--) {
      try { doc.getCellPicturePropertiesByPath(s, ppi, path(cp), ci); } catch { continue; }
      doc.deleteCellPictureControlByPath(s, ppi, path(cp), ci);
      picParas.add(cp);
      removed++;
    }
  }
  // 글이 없는 칸(그림 상자)이면 빈 문단을 모두, 글이 있으면 그림이 있던 문단만 걷는다
  const hasText = Array.from({ length: count() }, (_, cp) => len(cp)).some((n) => n > 0);
  for (let cp = count() - 1; cp >= 0; cp--) {
    if (count() === 1) break;
    if (len(cp) !== 0 || (hasText && !picParas.has(cp))) continue;
    if (cp > 0) doc.deleteRangeInCell(s, ppi, ctrl, cell, cp - 1, len(cp - 1), cp, 0);
    else doc.deleteRangeInCell(s, ppi, ctrl, cell, 0, 0, 1, 0);
  }
  return removed;
}

function paraTextAt(doc, s, p) {
  try { return doc.getTextRange(s, p, 0, doc.getParagraphLength(s, p)); } catch { return ''; }
}

/**
 * insert_paragraphs 를 글 없는 문단(빈 문단, 표나 그림만 든 문단) 뒤에 했을 때, 새 문단의 글자 모양을 이웃 본문에 맞춘다.
 * 새 문단은 앞 문단의 글자 모양을 물려받는데, 빈 문단의 글자 모양은 아무 값이나 남아 있어 소제목(12pt)을 물려받았다
 * (2026-10-02 가이드북 4절, 문단 모양은 본문과 같아 화면에서 안 보였다). 앞뒤 15문단에서 문단 모양이 같은 글 문단이
 * 가장 많이 쓰는 글자 모양(글자 수 기준)으로 맞추고 result.style 에 알린다.
 */
function fixInsertedCharShape(doc, s, after, n, result) {
  if (!n) return;
  const J = (x) => (typeof x === 'string' ? JSON.parse(x) : x);
  const cs = (p) => J(doc.getCharPropertiesAt(s, p, 0));
  const ps = (p) => J(doc.getParaPropertiesAt(s, p)).paraShapeId;
  const first = after + 1;
  const want = ps(first);
  const count = doc.getParagraphCount(s);
  const votes = new Map();
  for (let p = Math.max(0, after - 15); p < Math.min(count, first + n + 15); p++) {
    if (p >= first && p < first + n) continue;
    const t = paraTextAt(doc, s, p).trim();
    if (!t || ps(p) !== want) continue;
    const id = cs(p).charShapeId;
    votes.set(id, (votes.get(id) || 0) + t.length);
  }
  if (!votes.size) return;
  const target = [...votes.entries()].sort((a, b) => b[1] - a[1])[0][0];
  const before = cs(first);
  if (before.charShapeId === target) return;
  for (let p = first; p < first + n; p++) {
    const len = doc.getParagraphLength(s, p);
    if (len > 0) doc.setCharShapeId(s, p, 0, len, target);
  }
  const after_ = cs(first);
  result.style = `새 문단 글자 모양을 이웃 본문에 맞춤(${before.fontSize / 100}pt → ${after_.fontSize / 100}pt) — 앞 문단 p${after} 이 글 없는 문단이라 그 글자 모양을 따르지 않았다`;
}

/** 없는 메서드를 불렀을 때 비슷한 이름(`getPageCount` → `pageCount`). */
function similarMethods(doc, name) {
  const key = name.toLowerCase().replace(/^(get|set)/, '');
  const all = Object.getOwnPropertyNames(Object.getPrototypeOf(doc)).filter((n) => typeof doc[n] === 'function');
  const hits = all.filter((n) => n.toLowerCase().includes(key)).slice(0, 5);
  return hits.length ? ` — 비슷한 것: ${hits.join(', ')}` : '';
}

/** 작업 한 건 중 tool, doc 을 처리한다. 다른 종류면 undefined(호출자가 처리) */
export function stepCore(doc, op) {
  if (op.tool && EXTRA_RUN[op.tool]) return EXTRA_RUN[op.tool](doc, op.args || {});
  const nested = op.tool ? runNestedTool(doc, op.tool, op.args || {}) : null;
  if (nested) return nested;
  if (op.tool === 'search_text') return searchWithNested(doc, op.args || {});
  if (op.tool) {
    const afterEmpty = op.tool === 'insert_paragraphs' && !paraTextAt(doc, op.args?.section ?? 0, op.args?.after_para ?? -1).trim();
    const { result } = runTool(doc, op.tool, op.args || {});
    if (!result.ok) throw new Error(result.error);
    if (afterEmpty) fixInsertedCharShape(doc, op.args.section ?? 0, op.args.after_para, (op.args.texts || []).length, result);
    return result;
  }
  if (op.doc) {
    const fn = doc[op.doc];
    if (typeof fn !== 'function') throw new Error(`HwpDocument 에 없는 메서드: ${op.doc}${similarMethods(doc, op.doc)}`);
    // JSON 객체나 배열 문자열은 공백 없이 다시 직렬화한다. rhwp 의 json_str 은 `"headType":"Bullet"` 꼴만
    // 찾아, 파이썬 json.dumps 기본값(`": "`)으로 만든 문자열은 문자열 키가 오류 없이 무시됐다(2026-10-02
    // 가이드북 세션). 빌드가 매개변수 이름을 지워 `_json` 으로는 못 가린다 — 글을 받는 메서드는 건드리지 않는다
    const textual = /text|html|search|replace|field|memo|caption/i.test(op.doc);
    const args = (op.a || []).map((x) => {
      if (x !== null && typeof x === 'object') return JSON.stringify(x);
      if (!textual && typeof x === 'string' && /^\s*[{[]/.test(x)) {
        try { return JSON.stringify(JSON.parse(x)); } catch { return x; }
      }
      return x;
    });
    return parseMaybe(fn.apply(doc, args));
  }
  return undefined;
}

export { parseMaybe, EXTRA_TOOLS, EXTRA_RUN, runNestedTool, searchWithNested, paraTextAt, fixInsertedCharShape, similarMethods, clearCellPictures };
