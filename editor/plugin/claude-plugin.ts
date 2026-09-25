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
import { TOOLS, listTables, outline, resolveTarget, runTool } from './doc-tools.js';
import { detectDocType, findSlots, inspect } from './doc-rules.js';
import { modelOf } from './collab-ops.js';
import { installHancomKeys } from './hancom-keys';

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

      const mutating = (op) => {
        if (op.tool) return !READ_TOOLS.has(op.tool);
        if (op.m) return isMutating(op.m);
        if (op.doc) return !READ_DOC.test(op.doc);
        return Boolean(op.run);
      };

      const step = (doc, op, i) => {
        try {
          if (op.tool) {
            const { result } = runTool(doc, op.tool, op.args || {});
            if (!result.ok) throw new Error(result.error);
            return result;
          }
          if (op.m) {
            const fn = ctrl[op.m];
            if (typeof fn !== 'function') throw new Error(`HwpCtrl 에 없는 메서드: ${op.m}`);
            return fn.apply(ctrl, op.a || []);
          }
          if (op.run) return ctrl.Run(op.run);
          if (op.doc) {
            const fn = doc[op.doc];
            if (typeof fn !== 'function') throw new Error(`HwpDocument 에 없는 메서드: ${op.doc}`);
            const args = (op.a || []).map((x) => (x !== null && typeof x === 'object' ? JSON.stringify(x) : x));
            return parseMaybe(fn.apply(doc, args));
          }
          throw new Error('op 에 tool, doc, m, run 중 하나가 있어야 한다');
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
        tools: () => TOOLS,
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
