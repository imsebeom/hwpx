// @ts-nocheck
/**
 * F5 로 여러 셀을 고른 뒤 Ctrl+E(지우기)를 누르면 무엇을 지울지 묻는다(2026-09-27 사용자 요청).
 * rhwp 는 셀 선택 모드에서 Ctrl+E 를 받으면 모드를 풀고 텍스트 선택 지우기로 넘겨 아무 일도 하지 않았다.
 *   - 셀 내용만 지우기: 고른 칸마다 문단을 모두 비운다(칸은 남는다)
 *   - 줄 지우기 / 칸 지우기: 고른 칸이 걸친 줄(행) / 칸(열)을 지운다. rhwp 엔진에는 행, 열 삭제만 있고
 *     임의의 칸만 떼어 내는 기능은 없다. 표 속 표에서는 내용 지우기만 한다.
 * 어느 것이든 되돌리기 한 번에 돌아간다.
 */
import { ModalDialog } from '@/ui/dialog';

const isCtrlE = (e) =>
  (e.ctrlKey || e.metaKey) && !e.altKey && !e.shiftKey &&
  (e.code === 'KeyE' || (!e.code && e.keyCode === 69));

class CellEraseDialog extends ModalDialog {
  constructor(nested, onChoose) {
    super('셀 지우기', 300);
    this.nested = nested;
    this.onChoose = onChoose;
    // 한/글처럼 괄호 안 글쇠로 바로 고른다
    this.keyPick = (e) => {
      const k = { KeyC: 'content', KeyR: 'rows', KeyL: 'cols' }[e.code];
      const r = k && this.radios?.find((x) => x.value === k && !x.disabled);
      if (r && !e.ctrlKey && !e.altKey) { r.checked = true; e.preventDefault(); }
    };
  }
  createBody() {
    const body = document.createElement('div');
    const opts = [
      ['content', '셀 내용만 지우기(C)'],
      ['rows', '줄 지우기(R)'],
      ['cols', '칸 지우기(L)'],
    ];
    this.radios = opts.map(([value, text], i) => {
      const label = document.createElement('label');
      label.style.cssText = 'display:block;padding:4px 2px;cursor:pointer';
      const r = document.createElement('input');
      r.type = 'radio';
      r.name = 'claude-cell-erase';
      r.value = value;
      r.checked = i === 0;
      r.disabled = this.nested && value !== 'content';
      label.append(r, ` ${text}`);
      body.appendChild(label);
      return r;
    });
    return body;
  }
  show() {
    // 기본 대화상자가 document 에서 키를 먼저 가로채므로 그보다 앞서 등록한다.
    // 초점은 기본대로 확인 단추에 둔다(라디오에 두면 Enter 가 확인으로 가지 않는다)
    document.addEventListener('keydown', this.keyPick, true);
    super.show();
  }
  hide() {
    document.removeEventListener('keydown', this.keyPick, true);
    super.hide();
  }
  onConfirm() {
    const picked = this.radios.find((r) => r.checked)?.value ?? 'content';
    this.onChoose(picked);
  }
}

function cellPath(block, cellIdx) {
  if (block.cellPath) {
    const p = block.cellPath.map((x) => ({ ...x }));
    p[p.length - 1] = { ...p[p.length - 1], cellIndex: cellIdx, cellParaIndex: 0 };
    return p;
  }
  return [{ controlIndex: block.ci, cellIndex: cellIdx, cellParaIndex: 0 }];
}

function eraseContents(ih, block) {
  ih.executeOperation({
    kind: 'snapshot',
    operationType: 'clearCellBlockContents',
    operation: (wasm) => {
      for (const c of block.cellIndices) {
        const pj = JSON.stringify(cellPath(block, c));
        const n = wasm.getCellParagraphCountByPath(block.sec, block.ppi, pj);
        if (n <= 0) continue;
        const last = JSON.stringify(cellPath(block, c).map((x, i, a) => (i === a.length - 1 ? { ...x, cellParaIndex: n - 1 } : x)));
        const lastLen = wasm.getCellParagraphLengthByPath(block.sec, block.ppi, last);
        if (n === 1 && lastLen === 0) continue;
        wasm.deleteRangeInCellByPath(block.sec, block.ppi, pj, 0, 0, n - 1, lastLen);
      }
      return ih.getCursorPosition();
    },
  });
}

function eraseLines(ih, block, kind) {
  const wasm = ih.wasm;
  const lines = new Set();
  for (const c of block.cellIndices) {
    const info = wasm.getCellInfo(block.sec, block.ppi, block.ci, c);
    const [start, span] = kind === 'rows' ? [info.row, info.rowSpan] : [info.col, info.colSpan];
    for (let i = start; i < start + Math.max(1, span); i++) lines.add(i);
  }
  const dims = wasm.getTableDimensions(block.sec, block.ppi, block.ci);
  const total = kind === 'rows' ? dims.rowCount : dims.colCount;
  // 셀 선택을 먼저 풀어야 지운 칸을 가리키는 선택 표시가 남지 않는다
  ih.cursor.exitCellSelectionMode();
  ih.cellSelectionRenderer?.clear();
  const pos = ih.getCursorPosition();
  ih.executeOperation({
    kind: 'snapshot',
    operationType: kind === 'rows' ? 'deleteTableRow' : 'deleteTableColumn',
    operation: (w) => {
      if (lines.size >= total) {
        w.deleteTableControl(block.sec, block.ppi, block.ci);   // 모든 줄(칸)을 지우면 표가 남지 않는다
      } else {
        for (const i of [...lines].sort((a, b) => b - a)) {
          if (kind === 'rows') w.deleteTableRow(block.sec, block.ppi, block.ci, i);
          else w.deleteTableColumn(block.sec, block.ppi, block.ci, i);
        }
      }
      return pos;
    },
  });
}

export function installCellBlockErase(getInputHandler) {
  window.addEventListener('keydown', (e) => {
    if (!isCtrlE(e)) return;
    const ih = getInputHandler();
    const block = ih?.getSelectedCellBlock?.();
    if (!block || !block.cellIndices.length) return;
    e.preventDefault();
    e.stopImmediatePropagation();
    const dialog = new CellEraseDialog(Boolean(block.cellPath), (picked) => {
      try {
        if (picked === 'content') eraseContents(ih, block);
        else eraseLines(ih, block, picked);
      } catch (err) {
        console.warn('[claude] 셀 지우기 실패:', err);
      }
    });
    dialog.afterClose = () => ih.focus?.();
    dialog.show();
  }, true);
}
