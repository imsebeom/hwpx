// @ts-nocheck
/**
 * 글을 고르면 상태 표시줄에 고른 글자 수를 「x글자(공란 제외 y글자)」로 보인다(2026-10-25 사용자 요청).
 * 선택 사각형이나 칸 블록(F5)을 그리거나 지울 때 다음 프레임에 한 번 센다.
 *   - 본문, 칸, 글상자 안 선택: 엔진 claudeSelectionCharCount(패치 sel-char-count-wasm)가 범위 안 표, 글상자, 캡션 글까지 센다
 *   - 칸 블록: 고른 칸마다 칸 글 전체
 *   - 머리말/꼬리말, 각주/미주 안 선택: 그 문단 글을 잘라 센다
 * 문단 끝은 세지 않고, 공란은 빈칸, 탭 같은 공백 문자다.
 */
import { SelectionRenderer } from '@/engine/selection-renderer';
import { CellSelectionRenderer } from '@/engine/cell-selection-renderer';
import { cellParaIndexOf, cellAxisPath } from '@/engine/command';

const END = 0xffffffff;   // 문단 끝까지(엔진이 끝에 붙은 개체도 넣는다)

function countText(t, n) {
  for (const c of t) {
    if (c === '\n' || c === '\r') continue;
    n[0] += 1;
    if (!/\s/.test(c)) n[1] += 1;
  }
}

/** 문단별 글 배열에서 (p0, o0) ~ (p1, o1) 를 센다 */
function countTexts(texts, p0, o0, p1, o1, n) {
  for (let p = p0; p <= p1; p++) {
    const chars = [...(texts(p) ?? '')];
    countText(chars.slice(p === p0 ? o0 : 0, p === p1 ? o1 : chars.length).join(''), n);
  }
}

const engine = (ih, ...a) => JSON.parse(ih.wasm.doc.claudeSelectionCharCount(...a));
const add = (n, m) => { n[0] += m[0]; n[1] += m[1]; };

/** 지금 고른 것의 [공란 포함, 공란 제외]. 고른 것이 없거나 셀 수 없는 선택이면 null */
function selectionCount(ih) {
  const cur = ih.cursor, wasm = ih.wasm;
  const n = [0, 0];

  const block = ih.getSelectedCellBlock?.();
  if (block?.cellIndices?.length) {
    for (const c of block.cellIndices) {
      const path = block.cellPath
        ? block.cellPath.map((x, i, a) => (i === a.length - 1 ? { ...x, cellIndex: c, cellParaIndex: 0 } : x))
        : [{ controlIndex: block.ci, cellIndex: c, cellParaIndex: 0 }];
      const pj = JSON.stringify(path);
      const last = wasm.getCellParagraphCountByPath(block.sec, block.ppi, pj) - 1;
      if (last >= 0) add(n, engine(ih, block.sec, block.ppi, pj, 0, 0, last, END));
    }
    return n;
  }

  const hf = cur.getHeaderFooterSelectionOrdered?.();
  if (hf) {
    const { start: s, end: e } = hf;
    countTexts((p) => JSON.parse(wasm.getHeaderFooterParaInfo(s.sectionIdx, s.isHeader, s.applyTo, p)).text,
      s.paraIdx, s.charOffset, e.paraIdx, e.charOffset, n);
    return n;
  }

  const fn = cur.getFootnoteSelectionOrdered?.();
  if (fn) {
    const texts = wasm.getFootnoteInfo(cur.fnSectionIdx, cur.fnParaIdx, cur.fnControlIdx).texts ?? [];
    countTexts((p) => texts[p], fn.start.fnParaIdx, fn.start.charOffset, fn.end.fnParaIdx, fn.end.charOffset, n);
    return n;
  }

  const sel = ih.getSelection?.();
  if (!sel) return null;
  const { start, end } = sel;
  const inCell = start.parentParaIndex !== undefined;
  if (inCell !== (end.parentParaIndex !== undefined)) return null;   // 본문과 칸에 걸친 선택은 음영도 그리지 않는다
  if (inCell) {
    const path = cellAxisPath(start), endPath = cellAxisPath(end);
    if (start.parentParaIndex !== end.parentParaIndex || path.length !== endPath.length
      || path.some((p, i) => p.controlIndex !== endPath[i].controlIndex || p.cellIndex !== endPath[i].cellIndex)) return null;
    add(n, engine(ih, start.sectionIndex, start.parentParaIndex, JSON.stringify(path),
      cellParaIndexOf(start), start.charOffset, cellParaIndexOf(end), end.charOffset));
    return n;
  }
  for (let s = start.sectionIndex; s <= end.sectionIndex; s++) {
    const first = s === start.sectionIndex;
    const lastSec = s === end.sectionIndex;
    add(n, engine(ih, s, -1, '[]', first ? start.paragraphIndex : 0, first ? start.charOffset : 0,
      lastSec ? end.paragraphIndex : wasm.getParagraphCount(s) - 1, lastSec ? end.charOffset : END));
  }
  return n;
}

export function installSelectionCount(getInputHandler) {
  const mode = document.getElementById('sb-mode');
  if (!mode) return;
  const label = document.createElement('span');
  label.id = 'sb-selection-count';
  label.className = 'stb-item';
  label.hidden = true;
  const divider = document.createElement('span');
  divider.className = 'stb-divider';
  divider.hidden = true;
  mode.after(divider, label);

  // 쪽을 넘길 때도 선택 사각형을 다시 그리므로, 고른 범위가 그대로면 다시 세지 않는다
  let queued = false;
  let lastKey = '';
  const keyOf = (ih) => {
    const cur = ih.cursor;
    const block = ih.getSelectedCellBlock?.();
    return JSON.stringify([
      block?.cellIndices?.length ? block : null,
      cur.getHeaderFooterSelectionOrdered?.(),
      cur.getFootnoteSelectionOrdered?.(),
      cur.getFootnoteSelectionOrdered?.() ? [cur.fnSectionIdx, cur.fnParaIdx, cur.fnControlIdx] : null,
      ih.getSelection?.(),
    ], (k, v) => (k === 'cursorRect' ? undefined : v));
  };
  const update = () => {
    queued = false;
    const ih = getInputHandler();
    if (!ih) return;
    let n = null;
    try {
      const key = keyOf(ih);
      if (key === lastKey) return;
      lastKey = key;
      n = selectionCount(ih);
    } catch (e) {
      console.warn('[claude] 고른 글자 수를 못 셌다:', e);
    }
    const show = !!n && n[0] > 0;
    label.hidden = divider.hidden = !show;
    if (show) label.textContent = `${n[0].toLocaleString()}글자(공란 제외 ${n[1].toLocaleString()}글자)`;
  };
  const schedule = () => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(update);
  };
  for (const R of [SelectionRenderer, CellSelectionRenderer]) {
    for (const name of ['render', 'clear']) {
      const orig = R.prototype[name];
      R.prototype[name] = function (...args) {
        const r = orig.apply(this, args);
        schedule();
        return r;
      };
    }
  }
}
