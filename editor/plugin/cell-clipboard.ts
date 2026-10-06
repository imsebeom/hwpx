// @ts-nocheck
/**
 * 칸 블록(F5 로 고른 칸 하나 또는 여러 칸)에서 Ctrl+C, Ctrl+X, Ctrl+V 가 되게 한다(2026-10-06 사용자 요청
 * 「여러 셀이든 한 셀이든 ctrl-c v x 이런게 되야지」).
 * rhwp 는 칸 선택 중에 이 키를 받으면 칸 선택을 풀고 글 선택 복사로 넘겨, 고른 칸이 하나도 복사되지 않았다.
 *
 *   복사    칸마다 서식 있는 HTML 과 글을 모은다. 시스템 클립보드에는 탭으로 나눈 글과 <table> HTML 을 함께 둔다
 *           (엑셀, 한/글에 붙여도 칸이 나뉜다)
 *   오려두기 복사한 뒤 고른 칸의 내용만 지운다(칸은 남는다)
 *   붙이기  칸 블록 또는 커서가 있는 칸을 왼쪽 위로 삼아 칸마다 내용을 바꾼다. 칸 하나를 복사해 여러 칸을 고르고 붙이면
 *           고른 칸 모두에 넣는다. 밖에서 복사한 표 HTML, 탭으로 나눈 글도 칸에 나눠 넣는다. 표 밖으로 넘치는 칸, 병합으로
 *           가려진 자리는 건너뛴다
 * 오려두기와 붙이기는 되돌리기 한 번에 돌아간다. 키는 막지 않고 rhwp 의 칸 선택 해제만 막아 브라우저의 copy, cut, paste
 * 이벤트가 그대로 일어나게 한다 — 그 이벤트에서 클립보드를 동기로 읽고 쓰므로 권한 창이 뜨지 않는다.
 */

const MARK = 'data-claude-cells';
let memory = null; // { id, rows, cols, cells: [{ r, c, rs, cs, html, text }] }

const isKey = (e, code, kc) =>
  (e.ctrlKey || e.metaKey) && !e.altKey && !e.shiftKey && (e.code === code || (!e.code && e.keyCode === kc));

function pathFor(block, cellIdx, para = 0) {
  if (block.cellPath) {
    const p = block.cellPath.map((x) => ({ ...x }));
    p[p.length - 1] = { ...p[p.length - 1], cellIndex: cellIdx, cellParaIndex: para };
    return p;
  }
  return [{ controlIndex: block.ci, cellIndex: cellIdx, cellParaIndex: para }];
}

function tablePathJson(block) {
  // 표 자체를 가리키는 경로(…ByPath 의 표 단위 조회용)
  return JSON.stringify(pathFor(block, 0));
}

function cellInfo(wasm, block, idx) {
  return block.cellPath
    ? wasm.getCellInfoByPath(block.sec, block.ppi, JSON.stringify(pathFor(block, idx)))
    : wasm.getCellInfo(block.sec, block.ppi, block.ci, idx);
}

function cellCount(wasm, block) {
  const dims = block.cellPath
    ? wasm.getTableDimensionsByPath(block.sec, block.ppi, tablePathJson(block))
    : wasm.getTableDimensions(block.sec, block.ppi, block.ci);
  return dims.cellCount;
}

/** 칸 문단 수와 마지막 문단 길이 */
function cellExtent(wasm, block, idx) {
  const n = wasm.getCellParagraphCountByPath(block.sec, block.ppi, JSON.stringify(pathFor(block, idx)));
  if (n <= 0) return { n: 0, lastLen: 0 };
  const lastLen = wasm.getCellParagraphLengthByPath(block.sec, block.ppi, JSON.stringify(pathFor(block, idx, n - 1)));
  return { n, lastLen };
}

function cellText(wasm, block, idx) {
  const { n } = cellExtent(wasm, block, idx);
  const out = [];
  for (let p = 0; p < n; p++) {
    const pj = JSON.stringify(pathFor(block, idx, p));
    const len = wasm.getCellParagraphLengthByPath(block.sec, block.ppi, pj);
    out.push(len > 0 ? wasm.getTextInCellByPath(block.sec, block.ppi, pj, 0, len) : '');
  }
  return out.join('\n');
}

function cellHtml(wasm, block, idx) {
  const { n, lastLen } = cellExtent(wasm, block, idx);
  if (n === 0 || (n === 1 && lastLen === 0)) return '';
  try {
    return wasm.exportSelectionInCellHtmlByPath(block.sec, block.ppi, JSON.stringify(pathFor(block, idx)), 0, 0, n - 1, lastLen) || '';
  } catch {
    return '';
  }
}

const bodyOf = (html) => {
  const m = /<body[^>]*>([\s\S]*)<\/body>/i.exec(html);
  return (m ? m[1] : html).replace(/<!--(?:Start|End)Fragment-->/g, '');
};
const escapeHtml = (s) => s.replace(/[&<>"]/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[ch]);
const tsvCell = (s) => (/[\t\n"]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s);

/** 고른 칸들을 잘라 낸 칸 묶음으로 */
function collect(ih, block) {
  const wasm = ih.wasm;
  const infos = block.cellIndices.map((idx) => ({ idx, ...cellInfo(wasm, block, idx) }));
  const r0 = Math.min(...infos.map((x) => x.row));
  const c0 = Math.min(...infos.map((x) => x.col));
  const rows = Math.max(...infos.map((x) => x.row + Math.max(1, x.rowSpan))) - r0;
  const cols = Math.max(...infos.map((x) => x.col + Math.max(1, x.colSpan))) - c0;
  const cells = infos.map((x) => ({
    r: x.row - r0, c: x.col - c0, rs: Math.max(1, x.rowSpan), cs: Math.max(1, x.colSpan),
    html: cellHtml(wasm, block, x.idx), text: cellText(wasm, block, x.idx),
  }));
  return { id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`, rows, cols, cells };
}

function toClipboard(e, data) {
  const grid = Array.from({ length: data.rows }, () => Array(data.cols).fill(''));
  for (const x of data.cells) grid[x.r][x.c] = x.text;
  const tsv = grid.map((row) => row.map(tsvCell).join('\t')).join('\n');
  const rowsHtml = Array.from({ length: data.rows }, (_, r) => {
    const tds = data.cells.filter((x) => x.r === r).sort((a, b) => a.c - b.c).map((x) => {
      const span = `${x.rs > 1 ? ` rowspan="${x.rs}"` : ''}${x.cs > 1 ? ` colspan="${x.cs}"` : ''}`;
      const inner = x.html ? bodyOf(x.html) : escapeHtml(x.text).replace(/\n/g, '<br>');
      return `<td${span}>${inner}</td>`;
    });
    return `<tr>${tds.join('')}</tr>`;
  }).join('');
  const html = `<html><body><!--StartFragment--><table ${MARK}="${data.id}" border="1" style="border-collapse:collapse">${rowsHtml}</table><!--EndFragment--></body></html>`;
  e.clipboardData.setData('text/plain', tsv);
  e.clipboardData.setData('text/html', html);
}

/** 클립보드에서 칸 묶음을 읽는다 — 이 에디터에서 복사한 것이면 서식째, 아니면 표 HTML 이나 탭 글 */
function fromClipboard(e) {
  const html = e.clipboardData.getData('text/html') || '';
  const text = e.clipboardData.getData('text/plain') || '';
  const id = new RegExp(`${MARK}="([^"]+)"`).exec(html)?.[1];
  if (id && memory && memory.id === id) return memory;
  if (/<table[\s>]/i.test(html)) {
    const doc = new DOMParser().parseFromString(html, 'text/html');
    const table = doc.querySelector('table');
    if (table) {
      const cells = [];
      const taken = new Set();
      [...table.rows].forEach((tr, r) => {
        let c = 0;
        for (const td of tr.cells) {
          while (taken.has(`${r},${c}`)) c++;
          const rs = Math.max(1, td.rowSpan || 1), cs = Math.max(1, td.colSpan || 1);
          for (let i = 0; i < rs; i++) for (let j = 0; j < cs; j++) taken.add(`${r + i},${c + j}`);
          cells.push({ r, c, rs, cs, html: '', text: (td.innerText ?? td.textContent ?? '').replace(/\r/g, '').trim() });
          c += cs;
        }
      });
      if (cells.length) {
        return { id: null, rows: Math.max(...cells.map((x) => x.r + x.rs)), cols: Math.max(...cells.map((x) => x.c + x.cs)), cells };
      }
    }
  }
  if (text.includes('\t')) {
    const lines = text.replace(/\r/g, '').replace(/\n$/, '').split('\n');
    const cells = [];
    lines.forEach((line, r) => line.split('\t').forEach((t, c) => cells.push({ r, c, rs: 1, cs: 1, html: '', text: t.replace(/^"([\s\S]*)"$/, (_, s) => s.replace(/""/g, '"')) })));
    return { id: null, rows: lines.length, cols: Math.max(...lines.map((l) => l.split('\t').length)), cells };
  }
  return null;
}

function clearCell(wasm, block, idx) {
  const { n, lastLen } = cellExtent(wasm, block, idx);
  if (n === 0 || (n === 1 && lastLen === 0)) return;
  wasm.deleteRangeInCellByPath(block.sec, block.ppi, JSON.stringify(pathFor(block, idx)), 0, 0, n - 1, lastLen);
}

function fillCell(wasm, block, idx, src) {
  clearCell(wasm, block, idx);
  const pj = JSON.stringify(pathFor(block, idx));
  if (src.html) {
    wasm.pasteHtmlInCellByPath(block.sec, block.ppi, pj, 0, src.html);
  } else if (src.text) {
    const paras = src.text.split('\n');
    paras.forEach((t, i) => {
      if (i > 0) {
        const prev = JSON.stringify(pathFor(block, idx, i - 1));
        const len = wasm.getCellParagraphLengthByPath(block.sec, block.ppi, prev);
        wasm.splitParagraphInCellByPath(block.sec, block.ppi, prev, len);
      }
      if (t) wasm.insertTextInCellByPath(block.sec, block.ppi, JSON.stringify(pathFor(block, idx, i)), 0, t);
    });
  }
}

/** 칸 선택이 아니면 커서가 있는 칸을 한 칸짜리 블록으로 */
function caretCellBlock(ih) {
  const pos = ih.getCursorPosition?.();
  if (!pos || pos.isTextBox || pos.parentParaIndex === undefined || pos.parentParaIndex === null) return null;
  if (pos.cellPath && pos.cellPath.length > 1) {
    const path = pos.cellPath.map((x) => ({ ...x }));
    return { sec: pos.sectionIndex, ppi: pos.parentParaIndex, ci: path[0].controlIndex, cellIndices: [path[path.length - 1].cellIndex], cellPath: path };
  }
  if (pos.controlIndex === undefined || pos.cellIndex === undefined) return null;
  return { sec: pos.sectionIndex, ppi: pos.parentParaIndex, ci: pos.controlIndex, cellIndices: [pos.cellIndex] };
}

function paste(ih, block, data) {
  const wasm = ih.wasm;
  const total = cellCount(wasm, block);
  const at = new Map();
  for (let i = 0; i < total; i++) {
    const x = cellInfo(wasm, block, i);
    at.set(`${x.row},${x.col}`, i);
  }
  const picked = block.cellIndices.map((idx) => ({ idx, ...cellInfo(wasm, block, idx) }));
  const r0 = Math.min(...picked.map((x) => x.row));
  const c0 = Math.min(...picked.map((x) => x.col));
  const jobs = [];
  if (data.cells.length === 1 && picked.length > 1) {
    for (const x of picked) jobs.push([x.idx, data.cells[0]]);   // 한 칸을 여러 칸에 채운다
  } else {
    for (const src of data.cells) {
      const idx = at.get(`${r0 + src.r},${c0 + src.c}`);
      if (idx !== undefined) jobs.push([idx, src]);
    }
  }
  if (!jobs.length) return false;
  const pos = ih.getCursorPosition();
  ih.executeOperation({
    kind: 'snapshot',
    operationType: 'pasteCellBlock',
    operation: (w) => {
      for (const [idx, src] of jobs) fillCell(w, block, idx, src);
      return pos;
    },
  });
  return true;
}

export function installCellClipboard(getInputHandler) {
  // 1) 키: 칸 선택 중이면 rhwp 가 칸 선택을 풀지 못하게 막되 기본 동작(copy, cut, paste 이벤트)은 살린다
  window.addEventListener('keydown', (e) => {
    if (!(isKey(e, 'KeyC', 67) || isKey(e, 'KeyX', 88) || isKey(e, 'KeyV', 86))) return;
    const block = getInputHandler()?.getSelectedCellBlock?.();
    if (block && block.cellIndices.length) e.stopImmediatePropagation();
  }, true);

  const onCopyOrCut = (cut) => (e) => {
    const ih = getInputHandler();
    const block = ih?.getSelectedCellBlock?.();
    if (!block || !block.cellIndices.length || !e.clipboardData) return;
    e.preventDefault();
    e.stopImmediatePropagation();
    try {
      memory = collect(ih, block);
      toClipboard(e, memory);
      if (cut) {
        const pos = ih.getCursorPosition();
        ih.executeOperation({
          kind: 'snapshot',
          operationType: 'cutCellBlock',
          operation: (w) => {
            for (const idx of block.cellIndices) clearCell(w, block, idx);
            return pos;
          },
        });
      }
    } catch (err) {
      console.warn('[claude] 칸 복사 실패:', err);
    }
  };
  window.addEventListener('copy', onCopyOrCut(false), true);
  window.addEventListener('cut', onCopyOrCut(true), true);

  // 2) 붙이기: 칸 선택이면 언제나, 커서가 칸 안이면 칸 묶음(표 HTML, 탭 글)일 때만 가로챈다
  window.addEventListener('paste', (e) => {
    const ih = getInputHandler();
    if (!ih || !e.clipboardData) return;
    const selected = ih.getSelectedCellBlock?.();
    const block = selected && selected.cellIndices.length ? selected : caretCellBlock(ih);
    if (!block) return;
    const data = fromClipboard(e);
    if (!data) {
      if (!selected) return;   // 칸 안 커서에 보통 글 — rhwp 에 맡긴다
      const text = e.clipboardData.getData('text/plain') || '';
      if (!text) return;
      e.preventDefault();
      e.stopImmediatePropagation();
      paste(ih, block, { rows: 1, cols: 1, cells: [{ r: 0, c: 0, rs: 1, cs: 1, html: '', text: text.replace(/\r/g, '').replace(/\n$/, '') }] });
      return;
    }
    if (!selected && data.cells.length === 1 && !data.id) return;   // 칸 안 커서에 한 칸짜리 바깥 글은 보통 붙이기로
    e.preventDefault();
    e.stopImmediatePropagation();
    try {
      paste(ih, block, data);
    } catch (err) {
      console.warn('[claude] 칸 붙이기 실패:', err);
    }
  }, true);
}
