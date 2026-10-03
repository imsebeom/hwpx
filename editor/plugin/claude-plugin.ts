// @ts-nocheck
/**
 * rhwp-studio 플러그인 "claude" — 터미널의 Claude 가 보낸 JSON 명령을 studio 가 들고 있는
 * 바로 그 문서에 적용한다. setup.mjs 가 이 파일과 lib/*.js 를 rhwp-studio/src/plugin/ 으로 복사하고
 * main.ts 의 allowlist 에 createClaudePlugin(() => inputHandler) 로 등록한다.
 *
 * 명령 한 건(op)의 모양:
 *   { tool: "fill_by_label", args: {...} }          편집 도구 26종(lib/doc-tools.js). 도구마다 스냅샷 보호
 *   { doc: "insertText", a: [0, 3, 0, "본문"] }      WASM HwpDocument 메서드(439개)
 *   { m: "PutFieldText", a: ["기안자", "홍길동"] }   HwpCtrl 메서드
 *   { run: "BreakPara" }                            HwpCtrl Run 액션
 * doc 인자 중 객체는 JSON 문자열로 바꿔 넘기고, JSON 문자열 반환값은 파싱해 돌려준다.
 * 배치 하나가 트랜잭션 하나이고 undo 1스텝이다. 하나라도 실패하면 배치 전체가 되돌려진다.
 */
import { createHwpCtrl } from '../../../npm/hwpctrl-ocx/src/index.mjs';
import { createAdoptDocument, isMutating } from '../../../npm/hwpctrl-ocx/src/adapter.mjs';
import { TOOLS, clean, listTables, outline, resolveTarget, runTool } from './doc-tools.js';
import { detectDocType, findSlots, inspect } from './doc-rules.js';
import { modelOf } from './collab-ops.js';
import { installHancomKeys } from './hancom-keys';
import { installEditLog } from './edit-log';
import { TableCreateDialog } from '@/ui/table-create-dialog';
import { CharShapeDialog } from '@/ui/char-shape-dialog';
import { ParaShapeDialog } from '@/ui/para-shape-dialog';
import { TableCellPropsDialog } from '@/ui/table-cell-props-dialog';
import { installKCommands } from './k-commands';
import { installLogPanel } from './log-panel';
import { installColorPalettes } from './color-palette';
import { installParaPreview } from './para-preview';
import { installDialogEnter } from './dialog-enter';
import { installCellBlockErase } from './cell-block-erase';
import { installPictureCrop } from './picture-crop';

// 이름이 이렇게 시작하는 WASM 메서드는 문서를 바꾸지 않는다고 본다.
const READ_DOC = /^(get|search|export|render|is|has|list|find|measure|hitTest|pageCount)/;
const READ_TOOLS = new Set(['read_document', 'search_text']);

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
};

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

/**
 * 셀 블록 범위를 걸친 병합 셀이 모두 들어갈 때까지 넓힌다(한/글과 같게).
 * rhwp 의 getSelectedCellRange 는 시작 셀과 끝 셀의 첫 행, 첫 열만으로 사각형을 만들어, 병합 셀에서
 * 끝나거나 병합 셀을 반만 걸치면 선택이 드래그 방향에 따라 달라지고 셀 합치기가 조용히 실패했다.
 * 선택 그리기, 서식, 합치기가 모두 이 메서드를 거치므로 커서 인스턴스에서 감싼다.
 */
function installMergedCellRange(host, getInputHandler) {
  const expand = (cursor, range) => {
    const ctx = cursor.getCellTableContext?.();
    if (!range || !ctx || (ctx.cellPath?.length ?? 1) > 1) return range; // 셀 안 표는 그대로
    const cells = host.read((doc) => {
      const n = JSON.parse(doc.getTableDimensions(ctx.sec, ctx.ppi, ctx.ci)).cellCount;
      return Array.from({ length: n }, (_, i) => JSON.parse(doc.getCellInfo(ctx.sec, ctx.ppi, ctx.ci, i)));
    });
    let { startRow: r0, startCol: c0, endRow: r1, endCol: c1 } = range;
    for (let grown = true; grown; ) {
      grown = false;
      for (const c of cells) {
        const cr1 = c.row + c.rowSpan - 1;
        const cc1 = c.col + c.colSpan - 1;
        if (c.row > r1 || cr1 < r0 || c.col > c1 || cc1 < c0) continue; // 범위와 안 겹친다
        if (c.row < r0) { r0 = c.row; grown = true; }
        if (c.col < c0) { c0 = c.col; grown = true; }
        if (cr1 > r1) { r1 = cr1; grown = true; }
        if (cc1 > c1) { c1 = cc1; grown = true; }
      }
    }
    return { startRow: r0, startCol: c0, endRow: r1, endCol: c1 };
  };
  const patch = () => {
    const cursor = getInputHandler()?.cursor;
    if (!cursor) return false;
    if (cursor.__mergedRange) return true;
    const orig = cursor.getSelectedCellRange.bind(cursor);
    cursor.getSelectedCellRange = () => {
      const range = orig();
      try { return expand(cursor, range); } catch { return range; }
    };
    cursor.__mergedRange = true;
    return true;
  };
  if (!patch()) {
    const t = setInterval(() => { if (patch()) clearInterval(t); }, 200);
  }

  // 셀 블록에 줄 간격, 글자 크기 같은 서식을 넣어 셀 높이가 바뀌어도 선택 음영이 옛 자리에 남았다.
  // rhwp 는 document-changed 때 그림, 표 선택 표시만 다시 그리고 셀 선택은 빠뜨린다. 다음 프레임에 다시 그린다.
  host.events.on('document-changed', () => {
    requestAnimationFrame(() => {
      const ih = getInputHandler();
      if (ih?.cursor?.isInCellSelectionMode?.()) ih.updateCellSelection?.();
    });
  });
}

/**
 * 키보드로 만든 셀 안 선택(Home, Shift+End 등)은 위치에 cellPath 가 없고 평평한 좌표(controlIndex, cellIndex,
 * cellParaIndex)만 있다. 서식 명령(ApplyCharFormatCommand, 셀 문단 서식)은 cellPath 로만 경로를 만들어
 * 「경로가 비어있습니다」로 던졌다 — Alt+C 모양 붙이기, 글자 모양, 문단 모양 대화상자의 설정이 셀 안에서
 * 알림 없이 실패했다(2026-09-25 실측). rhwp 의 cellAxisPath 와 같은 규칙으로 1단 경로를 채운다
 * (평평한 좌표가 cellPath[0] 에서 오므로 1단에서는 실제 경로와 같다).
 */
function installCellPathFill(getInputHandler) {
  const fill = (p) => (p && p.parentParaIndex != null && p.cellIndex != null && !(p.cellPath?.length)
    ? { ...p, cellPath: [{ controlIndex: p.controlIndex, cellIndex: p.cellIndex, cellParaIndex: p.cellParaIndex ?? 0 }] }
    : p);
  const patch = () => {
    const cursor = getInputHandler()?.cursor;
    if (!cursor) return false;
    if (cursor.__cellPathFill) return true;
    const orig = cursor.getSelectionOrdered.bind(cursor);
    cursor.getSelectionOrdered = () => {
      const sel = orig();
      return sel ? { start: fill(sel.start), end: fill(sel.end) } : sel;
    };
    cursor.__cellPathFill = true;
    return true;
  };
  if (!patch()) {
    const t = setInterval(() => { if (patch()) clearInterval(t); }, 200);
  }
}

/**
 * 표 선을 마우스로 클릭하면 표를 개체로 고른다(한/글처럼). rhwp 는 선 위 mousedown 을 곧바로 크기 조절
 * 드래그로 잡고, 떼었을 때 움직임이 1 쪽 픽셀(75 HWPUNIT) 미만이고 바깥 선일 때만 표를 골랐다. 확대 화면에서는
 * 클릭할 때의 손떨림이 그 한도를 넘어 표 선택 대신 선이 조금씩 옮겨졌다(2026-09-26 편집 기록의 「셀 크기」).
 * 누른 자리에서 화면 4px 안에서 떼면 크기 조절을 하지 않고 표를 고른다. 안쪽 선도 같다.
 */
function installTableClickSelect(host, getInputHandler) {
  let down = null;
  const selectTable = (ih, ref) => {
    const c = ih.cursor;
    c.clearSelection();
    c.exitCellSelectionMode?.();
    ih.cellSelectionRenderer?.clear();
    ih.exitPictureObjectSelectionIfNeeded?.();
    // 끌기 상태의 표 참조가 표 속 표 경로(깊이 2 이상)를 들고 있으면 그 안쪽 표를 고른다(엔진, 스튜디오 패치 nested-table-*)
    c.enterTableObjectSelectionDirect(ref.sec, ref.ppi, ref.ci, ref.path?.length > 1 ? ref.path : undefined);
    ih.active = true;
    ih.caret?.hide();
    ih.fieldMarker?.hide();
    ih.selectionRenderer?.clear();
    ih.renderTableObjectSelection();
    ih.eventBus.emit('table-object-selection-changed', true);
    ih.eventBus.emit('command-state-changed');
    ih.textarea.focus();
  };
  /** 화면 좌표 → (쪽, 쪽 좌표). rhwp onClick 과 같은 계산 */
  const toPage = (ih, e) => {
    const sc = ih.container?.querySelector('#scroll-content');
    if (!sc) return null;
    const r = sc.getBoundingClientRect();
    const cx = e.clientX - r.left;
    const cy = e.clientY - r.top;
    const pg = ih.virtualScroll.getPageAtPoint(cx, cy);
    const zoom = ih.viewportManager.getZoom();
    return { pg, x: (cx - ih.virtualScroll.getPageLeftResolved(pg, sc.clientWidth)) / zoom, y: (cy - ih.virtualScroll.getPageOffset(pg)) / zoom, zoom };
  };
  window.addEventListener('mousedown', (e) => { down = { x: e.clientX, y: e.clientY }; }, true);
  // rhwp 의 클릭 처리가 표 바깥 윗선 클릭을 표 선택까지 보내지 않는 경우가 있다(2026-09-26 실측 — 커서도 안 움직인다).
  // 떼었을 때 움직임이 없고 표 바깥 선 근처(화면 5px)인데 표가 안 골라졌으면 고른다.
  window.addEventListener('mouseup', (e) => {
    if (e.button !== 0 || !down || Math.hypot(e.clientX - down.x, e.clientY - down.y) >= 4) return;
    const ih = getInputHandler();
    if (!ih?.cursor || ih.cursor.isInTableObjectSelection()) return;
    const p = toPage(ih, e);
    if (!p) return;
    const tol = 5 / p.zoom;
    let hit = null;
    try {
      for (const t of host.read((doc) => listTables(doc))) {
        let b;
        try { b = ih.wasm.getTableBBoxAtPage(t.section, t.para, t.ctrl, p.pg); } catch { continue; }
        if (!b || !b.width) continue;
        const inX = p.x >= b.x - tol && p.x <= b.x + b.width + tol;
        const inY = p.y >= b.y - tol && p.y <= b.y + b.height + tol;
        const nearH = inX && (Math.abs(p.y - b.y) <= tol || Math.abs(p.y - (b.y + b.height)) <= tol);
        const nearV = inY && (Math.abs(p.x - b.x) <= tol || Math.abs(p.x - (b.x + b.width)) <= tol);
        if (nearH || nearV) { hit = { sec: t.section, ppi: t.para, ci: t.ctrl }; break; }
      }
    } catch { return; }
    if (hit) setTimeout(() => { if (!ih.cursor.isInTableObjectSelection()) selectTable(ih, hit); }, 0);
  }, true);
  const patch = () => {
    const ih = getInputHandler();
    if (!ih?.finishResizeDrag) return false;
    if (ih.__tableClick) return true;
    const orig = ih.finishResizeDrag.bind(ih);
    ih.finishResizeDrag = (e) => {
      const st = ih.resizeDragState;
      if (!st || !down || Math.hypot(e.clientX - down.x, e.clientY - down.y) >= 4) return orig(e);
      const ref = { ...st.tableRef };
      ih.cleanupResizeDrag();
      selectTable(ih, ref);
    };
    ih.__tableClick = true;
    return true;
  };
  if (!patch()) {
    const t = setInterval(() => { if (patch()) clearInterval(t); }, 200);
  }
}

/**
 * 표 안에 표 만들기(한/글 「표 안에서 Ctrl+N,T」). rhwp 의 table:create 는 셀 안에서 막혀 있고
 * (canExecute !inTable), 셀 안에 표를 만드는 엔진 API 도 없다. HTML 붙여넣기는 표를 탭 글로 펴 버린다.
 * 엔진이 셀에 표를 붙이는 것(내부 클립보드)은 지원하므로 한 스냅샷 안에서
 * ① 문서 끝에 임시 표를 셀 안쪽 폭에 맞춰 만들고 ② 내부 클립보드로 복사하고 ③ 임시 표와 그것이 더한 빈 문단을 지우고
 * ④ 커서 자리에 붙인다. 되돌리기 한 번으로 통째 취소된다. 내부 클립보드는 이 표로 바뀐다.
 */
function installNestedTableCreate(getInputHandler) {
  const createInCell = (ih, pos, rows, cols, options) => {
    ih.executeOperation({
      kind: 'snapshot',
      operationType: 'createTable',
      operation: (wasm) => {
        const doc = wasm.doc;
        const sec = pos.sectionIndex;
        const path = pos.cellPath?.length
          ? pos.cellPath
          : [{ controlIndex: pos.controlIndex, cellIndex: pos.cellIndex, cellParaIndex: pos.cellParaIndex ?? 0 }];
        // 셀 안쪽 폭(바깥 셀만 잰다. 표 속 표의 셀이면 엔진 기본 폭)
        let colWidths;
        if (path.length === 1) {
          const cp = JSON.parse(doc.getCellProperties(sec, pos.parentParaIndex, pos.controlIndex, pos.cellIndex));
          const inner = cp.width - cp.paddingLeft - cp.paddingRight - 283 * 2;
          if (inner > cols * 400) colWidths = Array(cols).fill(Math.floor(inner / cols));
        }
        const n = doc.getParagraphCount(sec);
        const last = n - 1;
        const res = JSON.parse(doc.createTableEx(JSON.stringify({
          ...(options ?? {}), sectionIdx: sec, paraIdx: last, charOffset: doc.getParagraphLength(sec, last),
          rowCount: rows, colCount: cols, ...(colWidths ? { colWidths } : {}),
        })));
        if (!res.ok) throw new Error('임시 표를 만들지 못했다');
        const added = doc.getParagraphCount(sec) - n;
        doc.copyControl(sec, res.paraIdx, '[]', res.controlIdx);
        doc.deleteTableControl(sec, res.paraIdx, res.controlIdx);
        for (let p = res.paraIdx + added - 1; p >= res.paraIdx && p > last; p--) {
          if (doc.getParagraphLength(sec, p) === 0) doc.deleteParagraph(sec, p);
        }
        if (path.length > 1) doc.pasteInternalInCellByPath(sec, pos.parentParaIndex, JSON.stringify(path), pos.charOffset);
        else doc.pasteInternalInCell(sec, pos.parentParaIndex, pos.controlIndex, pos.cellIndex, pos.cellParaIndex ?? 0, pos.charOffset);
        return { ...pos };
      },
    });
  };
  const patch = () => {
    const ih = getInputHandler();
    const def = ih?.dispatcher?.registry?.get?.('table:create');
    if (!def) return false;
    if (def.__nested) return true;
    const origExec = def.execute;
    def.canExecute = (ctx) => ctx.hasDocument;
    def.execute = (services, params) => {
      const ih2 = services.getInputHandler();
      const pos = ih2?.getCursorPosition?.();
      if (!pos || pos.parentParaIndex === undefined || pos.isTextBox) return origExec.call(def, services, params);
      const dialog = new TableCreateDialog();
      dialog.onApply = (rows, cols, options) => {
        try { createInCell(ih2, pos, rows, cols, options); } catch (e) { console.warn('[claude] 표 안에 표 만들기 실패:', e); }
        ih2.textarea?.focus();
      };
      dialog.show(params?.anchorEl);
    };
    def.__nested = true;
    return true;
  };
  if (!patch()) {
    const t = setInterval(() => { if (patch()) clearInterval(t); }, 200);
  }
}

/**
 * 도구 모음 단추 셋을 한/글처럼(2026-09-26).
 *  - 하이퍼링크: rhwp 의 단추에 data-cmd 가 없어 눌러도 아무 일이 없었다 → insert:hyperlink(k-commands.ts)
 *  - 수준▲▼: rhwp 는 「개요 N」 스타일 문단만 바꿨다 → 문단 번호, 글머리표 문단은 수준(paraLevel 0~9)을 바꾼다
 *  - 개체 속성: 그림, 표를 개체로 골랐을 때만 됐다 → 표 셀 안이면 표/셀 속성을 연다
 */
/**
 * F5 로 여러 셀을 고르고 대화상자로 서식을 바꾸면 첫 칸에만 들어가던 것(2026-09-27 실측, 3×4 표 전체 블록).
 * 툴바와 단축키는 rhwp 가 셀 블록을 대상으로 잡지만(getSelectedCellBlock) 대화상자 셋은 그 경로를 타지 않았다.
 *   - 글자 모양: 텍스트 선택이 없다고 대화상자를 열지 않았다 → 블록이면 applyCharFormat 으로
 *   - 문단 모양: 커서 문단 하나에 적용했다 → 블록이면 applyParaFormat 으로
 *   - 표/셀 속성: 커서 셀에만 setCellProperties 를 불렀다 → 커서 셀에서 바뀐 항목만 블록의 나머지 셀에도
 *     (같은 스냅샷 안이라 되돌리기 한 번에 함께 돌아간다)
 */
function installCellBlockDialogs(getInputHandler) {
  const blockOf = (ih) => {
    const b = ih?.getSelectedCellBlock?.();
    return b && b.cellIndices.length ? b : null;
  };
  const patch = () => {
    const ih = getInputHandler();
    const reg = ih?.dispatcher?.registry;
    const cs = reg?.get?.('format:char-shape');
    const ps = reg?.get?.('format:para-shape');
    if (!cs || !ps) return false;
    if (cs.__cellBlock) return true;
    const origCs = cs.execute;
    cs.execute = (services, params) => {
      const h = services.getInputHandler();
      if (!blockOf(h)) return origCs.call(cs, services, params);
      const dialog = new CharShapeDialog(services.wasm, services.eventBus);
      dialog.onApply = (mods) => {
        // fontName → fontId (원래 명령과 같게)
        if (mods.fontName) {
          const fontId = services.wasm.findOrCreateFontId(mods.fontName);
          if (fontId >= 0) mods.fontId = fontId;
          delete mods.fontName;
        }
        h.applyCharFormat(mods);
      };
      dialog.onClose = () => h.focus();
      dialog.show(h.getCharProperties());
    };
    const origPs = ps.execute;
    ps.execute = (services, params) => {
      const h = services.getInputHandler();
      if (!blockOf(h)) return origPs.call(ps, services, params);
      const dialog = new ParaShapeDialog(services.wasm, services.eventBus);
      dialog.onApply = (mods) => h.applyParaFormat(mods);
      dialog.onClose = () => h.focus();
      dialog.show(h.getParaProperties());
    };
    cs.__cellBlock = true;
    return true;
  };
  if (!patch()) {
    const t = setInterval(() => { if (patch()) clearInterval(t); }, 200);
  }

  const proto = TableCellPropsDialog.prototype;
  if (proto.__cellBlock) return;
  const origConfirm = proto.onConfirm;
  proto.onConfirm = function () {
    const { sec, ppi, ci } = this.tableCtx;
    const block = blockOf(getInputHandler());
    const others = block && block.sec === sec && block.ppi === ppi && block.ci === ci
      ? block.cellIndices.filter((i) => i !== this.cellIdx) : [];
    if (!others.length) return origConfirm.call(this);
    const wasm = this.wasm;
    const base = this.cellProps;
    const anchor = this.cellIdx;
    const setOrig = wasm.setCellProperties;
    wasm.setCellProperties = function (s, p, c, idx, props) {
      const r = setOrig.call(this, s, p, c, idx, props);
      if (idx === anchor && s === sec && p === ppi && c === ci) {
        const diff = {};
        for (const [k, v] of Object.entries(props)) {
          if (JSON.stringify(v) !== JSON.stringify(base[k])) diff[k] = v;
        }
        if (Object.keys(diff).some((k) => k.startsWith('padding'))) diff.applyInnerMargin = props.applyInnerMargin;
        if (Object.keys(diff).length) for (const i of others) setOrig.call(this, s, p, c, i, diff);
      }
      return r;
    };
    try {
      return origConfirm.call(this);
    } finally {
      delete wasm.setCellProperties;   // 인스턴스에 얹은 것만 걷어 프로토타입 메서드로 돌아간다
    }
  };
  proto.__cellBlock = true;
}

/**
 * rhwp 는 숨은 입력칸을 화면 밖(left:-9999px)에 둔다. Windows 입력기는 한자 후보 창을 입력칸 옆에 띄우므로
 * 한 글자 치고 한자 키를 눌러도 후보 창이 화면 밖에 떠 보이지 않았다(2026-10-04 사용자 보고).
 * 키를 누를 때마다 입력칸을 캐럿(조합 중이면 조합 상자) 자리로 옮긴다. 투명하고 클릭은 통과한다.
 */
function installImeAnchor(getInputHandler) {
  const place = (e) => {
    const ta = getInputHandler()?.textarea;
    if (!ta || e.target !== ta) return;
    const r = [...document.querySelectorAll('.caret-composition'), ...document.querySelectorAll('.caret')]
      .map((el) => el.getBoundingClientRect()).find((b) => b.height > 0);
    if (!r) return;
    Object.assign(ta.style, { left: `${r.left}px`, top: `${r.top}px`, height: `${r.height}px`, pointerEvents: 'none' });
  };
  window.addEventListener('keydown', place, true);
  window.addEventListener('compositionupdate', place, true);

  // 한자 키: 입력기가 조합 중인 「한」을 확정하고, 입력칸에서 그 글자를 지운 뒤 같은 글자로 조합을 새로 연다
  // (compositionend 「한」 → deleteContentBackward → compositionstart → 「한」 → 「韓」, 2026-10-04 실측).
  // rhwp 는 확정 때 입력칸을 비워 지우기가 문서에 닿지 않아 「한韓」이 됐다. 새 조합이 열릴 때 확정된 글자를 문서에서 지운다.
  // 한자 키는 자판 설정에 따라 오른쪽 Ctrl(실측), HanjaMode, Lang2 로 온다.
  let hanjaAt = 0;
  let committed = '';
  window.addEventListener('keydown', (e) => {
    if (e.target !== getInputHandler()?.textarea || !e.isComposing) return;
    if (['ControlRight', 'Lang2'].includes(e.code) || e.key === 'HanjaMode') hanjaAt = performance.now();
  }, true);
  window.addEventListener('compositionend', (e) => {
    committed = e.target === getInputHandler()?.textarea && performance.now() - hanjaAt < 300 ? e.data || '' : '';
  }, true);
  window.addEventListener('compositionstart', (e) => {
    const ih = getInputHandler();
    if (!committed || e.target !== ih?.textarea) return;
    const n = [...committed].length;
    committed = '';
    for (let i = 0; i < n; i++) ih.handleBackspace(ih.cursor.getPosition(), ih.cursor.isInCell());
  }, true);
}

function installToolbarFixes(getInputHandler) {
  let wired = false;
  const wire = () => {
    const btn = [...document.querySelectorAll('.tb-btn')].find((b) => b.title === '하이퍼링크' && !b.dataset.cmd);
    if (!btn) return;
    btn.dataset.cmd = 'insert:hyperlink';
    const go = (e) => { e.preventDefault(); getInputHandler()?.dispatcher?.dispatch('insert:hyperlink', { anchorEl: btn }); };
    btn.addEventListener('mousedown', go);
    btn.addEventListener('click', (e) => { if (e.detail === 0) go(e); });
    wired = true;
  };
  const patch = () => {
    const ih = getInputHandler();
    const reg = ih?.dispatcher?.registry;
    if (!reg || !ih.changeOutlineLevel) return false;
    if (!wired) wire();
    if (ih.__toolbarFix) return true;
    const origLevel = ih.changeOutlineLevel.bind(ih);
    ih.changeOutlineLevel = (delta) => {
      const pos = ih.getCursorPosition();
      let style = null;
      try {
        style = pos.parentParaIndex !== undefined
          ? ih.wasm.getCellStyleAt(pos.sectionIndex, pos.parentParaIndex, pos.controlIndex, pos.cellIndex, pos.cellParaIndex)
          : ih.wasm.getStyleAt(pos.sectionIndex, pos.paragraphIndex);
      } catch { /* 스타일을 못 읽으면 아래 문단 수준으로 */ }
      if (style && /^개요\s*\d$/.test(style.name)) return origLevel(delta);
      const pp = ih.getParaProperties?.();
      if (!pp || !pp.headType || pp.headType === 'None') return undefined;   // 한/글도 번호 없는 문단은 그대로
      const level = Math.max(0, Math.min(9, (pp.paraLevel ?? 0) + delta));
      if (level !== (pp.paraLevel ?? 0)) ih.applyParaFormat({ paraLevel: level });
      return undefined;
    };
    const props = reg.get('format:object-properties');
    if (props && !props.__cellProps) {
      const origCan = props.canExecute;
      const origExec = props.execute;
      props.canExecute = (ctx) => origCan(ctx) || ctx.inTable;
      props.execute = (services, params) => {
        const h = services.getInputHandler();
        if (!h?.isInPictureObjectSelection?.() && !h?.isInTableObjectSelection?.() && h?.getCursorPosition?.().parentParaIndex !== undefined) {
          return h.dispatcher.dispatch('table:cell-props');
        }
        return origExec.call(props, services, params);
      };
      props.__cellProps = true;
    }
    ih.__toolbarFix = true;
    return true;
  };
  if (!patch()) {
    const t = setInterval(() => { if (patch()) clearInterval(t); }, 200);
  }
}

export function createClaudePlugin(getInputHandler) {
  return {
    id: 'claude',
    apiVersion: 1,

    activate(host) {
      const lease = host.borrowDocument();
      const ctrl = createHwpCtrl({
        wasm: null,
        doc: lease ? lease.handle : null,
        adoptDocument: createAdoptDocument(host),
        onSave: (bytes, fileName) => ({ bytes, fileName }),
      });
      host.onDocumentSwap((next) => { ctrl.setDocument?.(next.handle); });

      // 사용자 편집을 포함한 모든 문서 변경 수. 호스트가 이 값으로 사용자 편집을 감지한다.
      let mutations = 0;
      host.events.on('document-mutated', () => { mutations += 1; });
      host.onDocumentSwap(() => { mutations += 1; });

      // 한컴 한/글 기본 단축키(Ctrl+N 계열, 셀 안 Ctrl+A 등)
      installHancomKeys(host, getInputHandler);
      installMergedCellRange(host, getInputHandler);
      installCellPathFill(getInputHandler);
      installTableClickSelect(host, getInputHandler);
      installNestedTableCreate(getInputHandler);
      installKCommands(host, getInputHandler);
      installToolbarFixes(getInputHandler);
      installImeAnchor(getInputHandler);
      installCellBlockDialogs(getInputHandler);
      installColorPalettes(getInputHandler);
      installParaPreview();
      installDialogEnter();
      installCellBlockErase(getInputHandler);
      installPictureCrop(getInputHandler);
      installLogPanel();
      installEditLog(host, getInputHandler);   // 사용자 편집을 하나하나 /api/ops 로(`$E changes`)
      // 진단용: 디버그 포트로 붙었을 때 입력 처리기를 볼 수 있게(tests/cdp_eval.mjs 의 S.__claudeIH())
      (window as any).__claudeIH = getInputHandler;

      const mutating = (op) => {
        if (op.tool) return !READ_TOOLS.has(op.tool);
        if (op.m) return isMutating(op.m);
        if (op.doc) return !READ_DOC.test(op.doc);
        if (op.image) return true;
        return Boolean(op.run);
      };

      /**
       * 그림 넣기(cli.mjs image). run 의 JSON 으로는 그림 바이트를 넘길 수 없어 base64 로 받는다.
       * im: { base64, ext, naturalW, naturalH, at?(p7, T2r0c0), end?, widthMm?, desc? }.
       * 그림은 **그림만 담은 새 문단**으로 넣는다 — 좌표를 주면 그 문단 앞(end 면 칸의 마지막 문단이나 그 문단 뒤),
       * 좌표가 없으면 사용자 커서가 있는 문단 뒤. 글이 있는 문단 끝에 끼우면 rhwp 줄 나누기가 그림 높이를 첫 줄에 줘
       * 첫 줄 위에 빈칸이 생기고 그림이 눌려 그려졌다(2026-09-28 실측, 본문과 칸 모두).
       * 폭을 안 주면 원본 픽셀 크기(1px = 75 HWPUNIT)를 쓰되 본문 150mm, 칸은 칸 폭을 넘지 않게 줄인다.
       */
      const insertImage = (doc, im) => {
        const pos = im.at ? resolveTarget(doc, im.at) : getInputHandler()?.getCursorPosition?.();
        if (!pos) throw new Error(`그림 넣을 자리를 못 찾음: ${im.at ?? '커서'}`);
        const inCell = pos.parentParaIndex != null;
        const after = !im.at || im.end;
        const sec = pos.sectionIndex;
        // 새 빈 문단을 만들고 그 번호를 얻는다
        let target;
        let replaced = 0;
        if (inCell && im.replace) replaced = clearCellPictures(doc, sec, pos.parentParaIndex, pos.controlIndex, pos.cellIndex);
        const lone = inCell && im.replace && doc.getCellParagraphCount(sec, pos.parentParaIndex, pos.controlIndex, pos.cellIndex) === 1
          && doc.getCellParagraphLength(sec, pos.parentParaIndex, pos.controlIndex, pos.cellIndex, 0) === 0;
        if (lone) {
          target = 0;   // 그림만 있던 칸 — 남은 빈 문단 하나에 바로 넣는다(나누면 빈 문단이 또 남는다)
        } else if (inCell) {
          const [ppi, ci, cell] = [pos.parentParaIndex, pos.controlIndex, pos.cellIndex];
          let cp = pos.cellParaIndex ?? 0;
          if (im.at && im.end) cp = doc.getCellParagraphCount(sec, ppi, ci, cell) - 1;
          const off = after ? doc.getCellParagraphLength(sec, ppi, ci, cell, cp) : 0;
          doc.splitParagraphInCell(sec, ppi, ci, cell, cp, off);
          target = after ? cp + 1 : cp;
        } else {
          const p = pos.paragraphIndex;
          const off = after ? doc.getParagraphLength(sec, p) : 0;
          doc.splitParagraph(sec, p, off);
          target = after ? p + 1 : p;
        }
        let maxW = 42520;
        if (inCell) {
          try { maxW = Math.max(2000, JSON.parse(doc.getCellProperties(sec, pos.parentParaIndex, pos.controlIndex, pos.cellIndex)).width - 1200); } catch { /* 기본값 */ }
        }
        const width = im.widthMm ? Math.round((im.widthMm * 7200) / 25.4) : Math.min(im.naturalW * 75, maxW);
        const height = Math.round((width * im.naturalH) / im.naturalW);
        const bytes = Uint8Array.from(atob(im.base64), (c) => c.charCodeAt(0));
        const opts = {
          sectionIdx: sec,
          paraIdx: inCell ? pos.parentParaIndex : target,
          charOffset: 0,
          cellPath: inCell ? JSON.stringify([{ controlIndex: pos.controlIndex, cellIndex: pos.cellIndex, cellParaIndex: target }]) : '',
          width, height, naturalWidthPx: im.naturalW, naturalHeightPx: im.naturalH,
          extension: im.ext, description: im.desc ?? '',
          // 칸: 엔진 패치 cell-pic-inline 의 약속값. 칸 문단 안에 글자처럼 취급 그림으로 넣고 표 높이를 맞춘다
          ...(inCell ? { paperOffsetXHu: -2147483648, paperOffsetYHu: 0 } : {}),
        };
        const r = parseMaybe(doc.insertPictureEx(JSON.stringify(opts), bytes));
        // 본문은 스튜디오 그림 넣기처럼 글자처럼 취급으로 바꾼다(안 바꾸면 쪽 왼쪽 위 0,0 에 뜬다)
        if (r?.ok && !inCell) doc.setPictureProperties(sec, r.paraIdx, r.controlIdx, JSON.stringify({ treatAsChar: true }));
        return { ...r, ...(im.replace ? { replaced } : {}), at: inCell ? `셀 문단 ${target}` : `p${target}`, widthMm: +(width * 25.4 / 7200).toFixed(1), heightMm: +(height * 25.4 / 7200).toFixed(1), inCell };
      };

      const step = (doc, op, i) => {
        try {
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
          if (op.m) {
            const fn = ctrl[op.m];
            if (typeof fn !== 'function') throw new Error(`HwpCtrl 에 없는 메서드: ${op.m}`);
            return fn.apply(ctrl, op.a || []);
          }
          if (op.run) return ctrl.Run(op.run);
          if (op.image) return insertImage(doc, op.image);
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
          throw new Error('op 에 tool, doc, m, run, image 중 하나가 있어야 한다');
        } catch (e) {
          const err = new Error(`op[${i}] ${JSON.stringify(op).slice(0, 200)} 실패: ${e?.message ?? e}`);
          err.code = 'OP_FAILED';
          throw err;
        }
      };

      return {
        run(ops) {
          const list = Array.isArray(ops) ? ops : [ops];
          if (!list.some(mutating)) return host.read((doc) => list.map((op, i) => step(doc, op, i)));
          return host.transaction(`claude:run(${list.length})`, (tx) => {
            tx.deferPagination();
            const doc = tx.doc();
            return list.map((op, i) => step(doc, op, i));
          });
        },

        mutations: () => mutations,
        tools: () => [...TOOLS, ...EXTRA_TOOLS],
        outline: (opts) => host.read((doc) => outline(doc, opts || {})),
        model: () => host.read((doc) => modelOf(doc)),
        docType: () => host.read((doc) => detectDocType(doc)),
        slots: () => host.read((doc) => findSlots(doc)),
        inspect: (type) => host.read((doc) => inspect(doc, type)),

        /** 좌표(p12, T1r2c1)로 커서를 옮기고 그 문단이나 셀 글자를 선택한다. */
        goto(ref) {
          const ih = getInputHandler();
          const pos = ih && host.read((doc) => resolveTarget(doc, ref));
          if (!pos) return false;
          const { length, ...start } = pos;
          if (start.parentParaIndex == null) return ih.focusBodyParagraph(start.sectionIndex, start.paragraphIndex, length);
          ih.exitFootnoteModeForBodyNavigation();
          ih.cursor.clearSelection();
          ih.cursor.moveTo(start);
          if (length > 0) {
            ih.cursor.setAnchor();
            ih.cursor.moveTo({ ...start, charOffset: length });
          }
          ih.cursor.resetPreferredX();
          ih.active = true;
          ih.updateCaret(true);
          ih.focusTextarea();
          const rect = ih.cursor.getRect();
          if (rect) {
            const c = ih.container;
            const centerY = ih.virtualScroll.getPageOffset(rect.pageIndex) + rect.y * ih.viewportManager.getZoom();
            c.scrollTop = Math.max(0, Math.min(c.scrollHeight - c.clientHeight, centerY - c.clientHeight / 2));
          }
          return true;
        },

        /** 커서와 선택 영역. 표 셀 안이면 셀 좌표를, 선택이 있으면 그 글자를 준다. */
        cursor() {
          const ih = getInputHandler();
          if (!ih) return null;
          const pos = ih.getCursorPosition();
          const sel = ih.getSelection?.();
          let selectedText = '';
          if (sel) {
            selectedText = host.read((doc) => {
              const a = sel.start;
              const b = sel.end;
              if (a.parentParaIndex != null) {
                if (a.cellIndex !== b.cellIndex || a.cellParaIndex !== b.cellParaIndex) return '';
                return doc.getTextInCell(a.sectionIndex, a.parentParaIndex, a.controlIndex, a.cellIndex,
                  a.cellParaIndex, a.charOffset, b.charOffset - a.charOffset);
              }
              const parts = [];
              for (let p = a.paragraphIndex; p <= b.paragraphIndex; p++) {
                const len = doc.getParagraphLength(a.sectionIndex, p);
                const from = p === a.paragraphIndex ? a.charOffset : 0;
                const to = p === b.paragraphIndex ? b.charOffset : len;
                parts.push(to > from ? doc.getTextRange(a.sectionIndex, p, from, to - from) : '');
              }
              return parts.join('\n');
            });
          }
          let cellRef = null;
          if (pos.parentParaIndex != null) {
            // 셀 좌표를 doc-tools 표기(T1r2c1)로. 본문 표 목록에서 이 표의 번호를 찾는다.
            cellRef = host.read((doc) => {
              const info = parseMaybe(doc.getCellInfo(pos.sectionIndex, pos.parentParaIndex, pos.controlIndex, pos.cellIndex));
              const t = outlineTableId(doc, pos.sectionIndex, pos.parentParaIndex, pos.controlIndex);
              return t && info ? `${t}r${info.row}c${info.col}` : null;
            });
          }
          return {
            section: pos.sectionIndex,
            para: pos.paragraphIndex,
            charOffset: pos.charOffset,
            cell: pos.parentParaIndex != null
              ? { ref: cellRef, para: pos.parentParaIndex, ctrl: pos.controlIndex, cellIndex: pos.cellIndex, cellPara: pos.cellParaIndex, nested: (pos.cellPath?.length ?? 1) > 1 }
              : null,
            selectedText,
          };
        },
      };
    },
  };
}

/** 본문 표 번호(T1, T2 …). 셀 안 표는 번호가 없다(doc-tools listTables 규칙). */
function outlineTableId(doc, section, para, ctrl) {
  const t = listTables(doc).find((x) => x.section === section && x.para === para && x.ctrl === ctrl);
  return t?.id ?? null;
}

export default createClaudePlugin;
