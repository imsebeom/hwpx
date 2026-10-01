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
        if (inCell) {
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
        return { ...r, at: inCell ? `셀 문단 ${target}` : `p${target}`, widthMm: +(width * 25.4 / 7200).toFixed(1), heightMm: +(height * 25.4 / 7200).toFixed(1), inCell };
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
          if (op.image) return insertImage(doc, op.image);
          if (op.doc) {
            const fn = doc[op.doc];
            if (typeof fn !== 'function') throw new Error(`HwpDocument 에 없는 메서드: ${op.doc}`);
            const args = (op.a || []).map((x) => (x !== null && typeof x === 'object' ? JSON.stringify(x) : x));
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
