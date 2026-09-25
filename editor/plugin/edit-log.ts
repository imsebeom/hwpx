// @ts-nocheck
/**
 * 실시간 편집 기록. 사용자가 에디터에서 한 편집을 하나하나 좌표와 값으로 서버(/api/ops)에 보낸다.
 * Claude 는 `$E changes` 로 문서 전체를 비교하지 않고 이 기록만 읽어 무엇이 바뀌었는지 안다.
 *
 * 걸어 두는 자리:
 *  - rhwp 의 되돌리기 기록(CommandHistory) execute/undo/redo/recordWithoutExecute — 모든 편집이 여기를 지난다
 *  - 입력 처리기의 applyCharFormat/applyParaFormat — 무슨 서식을 무엇에서 무엇으로 바꿨는지(전 → 후)
 * 좌표는 outline 과 같다: 문단 p12:5(글자 위치), 셀 T6r1c3, 셀 블록 T6r1c3~r3c3.
 */
import { listTables } from './doc-tools.js';

const LABEL = {
  insertText: '입력', deleteText: '지움', deleteSelection: '선택 지움', insertLineBreak: '줄 바꿈', insertTab: '탭',
  splitParagraph: '문단 나눔', mergeParagraph: '문단 합침', mergeNextParagraph: '문단 합침',
  splitParagraphInCell: '문단 나눔', mergeParagraphInCell: '문단 합침', mergeNextParagraphInCell: '문단 합침',
  applyCharFormat: '글자 모양', applyParaFormat: '문단 모양', setCellBorderFill: '셀 테두리/배경',
  moveTable: '표 옮김', movePicture: '그림 옮김', moveShape: '도형 옮김', resizeObject: '개체 크기',
  setObjectProps: '개체 속성', setSectionProps: '구역 설정', changeZOrder: '개체 순서', setFormValue: '양식 값',
  // 스냅샷 작업(snapshot:<이름>)
  applyCharFormatCellBlock: '글자 모양(셀 블록)', applyCharFormatInHeaderFooter: '글자 모양(머리말/꼬리말)',
  applyParaFormatInFootnote: '문단 모양(각주)', applyParaFormatInHf: '문단 모양(머리말/꼬리말)', applyStyle: '스타일',
  mergeTableCells: '셀 합치기', splitTableCell: '셀 나누기', equalizeTableCellHeights: '셀 높이 같게',
  equalizeTableCellWidths: '셀 너비 같게', resizeTableCells: '셀 크기', resizeTableProportional: '표 크기',
  insertTableRow: '줄 추가', insertTableColumn: '칸 추가', deleteTableRow: '줄 지우기', deleteTableColumn: '칸 지우기',
  createTable: '표 만들기', deleteTable: '표 지우기', cutTable: '표 오려 두기', splitTable: '표 나누기',
  mergeTableWithNext: '표 붙이기', tableBlockCalc: '블록 계산', tableFormula: '계산식', toggleTableCaption: '캡션',
  cellNumberFormat: '셀 숫자 형식', formatCopyCellProps: '셀 모양 복사', pasteTableCellsTransposed: '행/열 바꿔 붙이기',
  pasteInternal: '붙이기', pasteHtml: '붙이기(서식)', pasteImage: '그림 붙이기', pasteControl: '개체 붙이기',
  replaceText: '바꾸기', replaceAll: '모두 바꾸기', insertPicture: '그림 넣기', insertEquation: '수식 넣기',
  equationEdit: '수식 고치기', deleteObject: '개체 지우기', cutObject: '개체 오려 두기', objectProps: '개체 속성',
  insertField: '필드 넣기', removeField: '필드 지우기', updateFieldProps: '필드 속성', addBookmark: '책갈피',
  deleteBookmark: '책갈피 지우기', renameBookmark: '책갈피 이름', pageBreak: '쪽 나누기', columnBreak: '단 나누기',
  pageSetup: '편집 용지', pageMargin: '쪽 여백', pageBorder: '쪽 테두리', pageHide: '감추기', columnSettings: '단 설정',
  setColumnDef: '단 설정', createHeaderFooter: '머리말/꼬리말 만들기', deleteHeaderFooter: '머리말/꼬리말 지우기',
  applyHfTemplate: '머리말/꼬리말 마당', deleteFootnote: '각주 지우기', endnoteShape: '미주 모양',
  insertNewNumber: '새 번호', deleteStyle: '스타일 지우기',
};

export function installEditLog(host, getInputHandler) {
  let queue = [];
  let timer = null;
  let formatCtx = null;     // 서식 호출 중이면 { kind, props, before, at }
  let tables = null;        // [{id, section, para, ctrl}] — 표 좌표 이름 캐시(문서가 바뀌면 비운다)

  const flush = () => {
    timer = null;
    if (!queue.length) return;
    const body = JSON.stringify({ ops: queue });
    queue = [];
    fetch('/api/ops', { method: 'POST', body }).catch(() => {});
  };
  const push = (entry) => {
    const last = queue[queue.length - 1];
    // 이어 치는 글자는 한 줄로 묶는다
    if (last && entry.type === 'insertText' && last.type === 'insertText' && last.act === entry.act &&
        last.src === entry.src && last.atKey === entry.atKey && last.end === entry.off && entry.t - last.t < 3000) {
      last.text += entry.text;
      last.end = entry.off + entry.text.length;
      last.t = entry.t;
    } else {
      queue.push(entry);
    }
    if (!timer) timer = setTimeout(flush, 200);
  };

  const tableId = (sec, para, ctrl) => {
    if (!tables) {
      try { tables = host.read((doc) => listTables(doc)); } catch { tables = []; }
    }
    return tables.find((t) => t.section === sec && t.para === para && t.ctrl === ctrl)?.id ?? `p${para}의 표`;
  };
  const cellRC = (sec, para, ctrl, cell) => {
    try {
      const i = host.read((doc) => JSON.parse(doc.getCellInfo(sec, para, ctrl, cell)));
      return `r${i.row}c${i.col}`;
    } catch { return `셀${cell}`; }
  };
  /** DocumentPosition → 'p12:5' / 'T6r1c3 p0:5' */
  const posText = (p) => {
    if (!p) return '';
    if (p.parentParaIndex != null && p.cellIndex != null) {
      if ((p.cellPath?.length ?? 1) > 1) return `p${p.parentParaIndex}의 표 속 표`;
      const t = tableId(p.sectionIndex, p.parentParaIndex, p.controlIndex);
      return `${t}${cellRC(p.sectionIndex, p.parentParaIndex, p.controlIndex, p.cellIndex)} p${p.cellParaIndex ?? 0}:${p.charOffset}`;
    }
    return `p${p.paragraphIndex}:${p.charOffset}`;
  };
  const targetText = (t) => (t.kind === 'cell'
    ? `${tableId(t.sec, t.parentPara, t.controlIdx)}${cellRC(t.sec, t.parentPara, t.controlIdx, t.cellIdx)}`
    : `p${t.para}`);
  /** 지금 편집이 걸린 자리: 셀 블록, 글 선택, 커서 */
  const whereNow = () => {
    const ih = getInputHandler();
    const c = ih?.cursor;
    if (!c) return '';
    const range = c.isInCellSelectionMode?.() ? c.getSelectedCellRange?.() : null;
    const ctx = range ? c.getCellTableContext?.() : null;
    if (range && ctx) {
      const t = tableId(ctx.sec, ctx.ppi, ctx.ci);
      const a = `r${range.startRow}c${range.startCol}`;
      const b = `r${range.endRow}c${range.endCol}`;
      return a === b ? `${t}${a}` : `${t}${a}~${b}`;
    }
    const sel = c.getSelectionOrdered?.();
    if (sel && (sel.start.charOffset !== sel.end.charOffset || sel.start.paragraphIndex !== sel.end.paragraphIndex ||
        sel.start.cellParaIndex !== sel.end.cellParaIndex)) {
      return `${posText(sel.start)} ~ ${posText(sel.end)}`;
    }
    return posText(ih.getCursorPosition?.());
  };

  const small = (v) => {
    if (v == null || typeof v !== 'object') return v;
    const s = JSON.stringify(v);
    return s.length > 120 ? `${s.slice(0, 117)}…` : v;
  };
  /** 명령 → 기록 한 줄 */
  const describe = (cmd, act) => {
    const type = String(cmd?.type ?? '?');
    const e = { t: Date.now(), act, type, src: type.startsWith('snapshot:plugin:claude') ? 'claude' : 'user' };
    const snap = type.startsWith('snapshot:') ? type.slice(9) : null;
    e.label = LABEL[type] ?? LABEL[snap] ?? (snap ? snap.replace(/^plugin:claude:/, 'Claude ') : type);
    try {
      if (cmd.position) {
        e.at = posText(cmd.position);
        e.atKey = e.at.replace(/:\d+$/, '');
        e.off = cmd.position.charOffset;
      }
      if (type === 'insertText') { e.text = cmd.text; e.end = e.off + cmd.text.length; }
      if (type === 'deleteText') { e.count = cmd.count; e.text = cmd.deletedText; e.dir = cmd.direction; }
      if (type === 'deleteSelection' && cmd.start) e.at = `${posText(cmd.start)} ~ ${posText(cmd.end)}`;
      if (type === 'applyCharFormat' && cmd.start) e.at = `${posText(cmd.start)} ~ ${posText(cmd.end)}`;
      if (type === 'applyParaFormat' && cmd.targets) {
        const ts = cmd.targets.map(targetText);
        e.at = ts.length > 4 ? `${ts.slice(0, 3).join(', ')} 외 ${ts.length - 3}` : ts.join(', ');
      }
    } catch { /* 필드가 달라도 기록은 남긴다 */ }
    if (formatCtx) {
      e.props = formatCtx.props;
      e.at = formatCtx.at || e.at;
      formatCtx.logged = true;
    }
    if (!e.at && act === 'do') e.at = whereNow();
    return e;
  };

  const hook = () => {
    const ih = getInputHandler();
    const h = ih?.history;
    if (!h || h.__editLog) return !!h;
    for (const [name, act] of [['execute', 'do'], ['recordWithoutExecute', 'do'], ['undo', 'undo'], ['redo', 'redo']]) {
      const orig = h[name].bind(h);
      h[name] = (...args) => {
        // undo/redo 는 스택 꼭대기 명령이 대상이다
        const target = act === 'undo' ? h.undoStack?.[h.undoStack.length - 1]
          : act === 'redo' ? h.redoStack?.[h.redoStack.length - 1] : args[0];
        const r = orig(...args);
        try { if (target && (act !== 'do' || !target.isNoOp?.())) push(describe(target, act)); } catch { /* 기록 실패가 편집을 막지 않는다 */ }
        return r;
      };
    }
    h.__editLog = true;

    // 서식: 무엇을 무엇에서 무엇으로 바꿨는지
    const wrapFormat = (name, kind, readBefore, propsAt = 0) => {
      const orig = ih[name]?.bind(ih);
      if (!orig) return;
      ih[name] = (...args) => {
        if (formatCtx) return orig(...args);   // 안쪽 호출은 바깥 것이 기록한다
        const props = args[propsAt];
        let before = {};
        try { before = readBefore() ?? {}; } catch { /* 없으면 후만 */ }
        const diff = {};
        for (const [k, v] of Object.entries(props ?? {})) {
          if (JSON.stringify(before[k]) !== JSON.stringify(v)) diff[k] = [small(before[k]), small(v)];
        }
        formatCtx = { kind, props: diff, at: whereNow(), logged: false };
        try {
          return orig(...args);
        } finally {
          const ctx = formatCtx;
          formatCtx = null;
          // 선택 없이 서식만 예약한 경우(다음 입력에 걸림) 등 기록에 안 남은 호출도 남긴다
          if (!ctx.logged && Object.keys(ctx.props).length) {
            push({ t: Date.now(), act: 'reserve', type: kind, label: `${kind === 'applyCharFormat' ? '글자 모양' : '문단 모양'} 예약`, src: 'user', at: ctx.at, props: ctx.props });
          }
        }
      };
    };
    wrapFormat('applyCharFormat', 'applyCharFormat', () => ih.getCharPropertiesAtCursor?.());
    wrapFormat('applyParaFormat', 'applyParaFormat', () => ih.getParaProperties?.());
    // 글자 모양, 문단 모양 대화상자의 설정은 이 두 함수로 온다(start, end, props)
    wrapFormat('applyCharPropsToRange', 'applyCharFormat', () => ih.getCharPropertiesAtCursor?.(), 2);
    wrapFormat('applyParaPropsToRange', 'applyParaFormat', () => ih.getParaProperties?.(), 2);
    return true;
  };
  if (!hook()) {
    const t = setInterval(() => { if (hook()) clearInterval(t); }, 200);
  }
  host.events.on('document-changed', () => { tables = null; });
  host.onDocumentSwap(() => { tables = null; queue = []; });
}
