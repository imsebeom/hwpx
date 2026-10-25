// @ts-nocheck
/**
 * 글을 고르면 상태 표시줄에 고른 글자 수를 「x글자(공란 제외 y글자)」로 보인다(2026-10-25 사용자 요청).
 * 선택 사각형을 그리거나 지울 때(SelectionRenderer.render, clear) 다음 프레임에 한 번 센다.
 * 본문 선택과 한 칸 안 선택만 센다. 문단 끝은 세지 않고, 본문 선택에 든 표나 글상자 안 글도 세지 않는다.
 * 공란은 빈칸, 탭 같은 공백 문자다. 머리말, 각주 안 선택과 칸 블록 선택(F5)에서는 보이지 않는다.
 */
import { SelectionRenderer } from '@/engine/selection-renderer';
import { cellParaIndexOf, cellAxisPath } from '@/engine/command';

function countText(t) {
  const chars = [...t.replace(/[\r\n]/g, '')];
  return [chars.length, chars.filter((c) => !/\s/.test(c)).length];
}

function selectedText(ih) {
  const sel = ih.getSelection?.();
  if (!sel) return null;
  const { start, end } = sel;
  const wasm = ih.wasm;
  const sec = start.sectionIndex;
  const inCell = start.parentParaIndex !== undefined;
  if (inCell !== (end.parentParaIndex !== undefined)) return null;
  const parts = [];
  if (inCell) {
    const path = cellAxisPath(start);
    const endPath = cellAxisPath(end);
    if (start.parentParaIndex !== end.parentParaIndex || path.length !== endPath.length
      || path.some((p, i) => p.controlIndex !== endPath[i].controlIndex || p.cellIndex !== endPath[i].cellIndex)) return null;
    const p0 = cellParaIndexOf(start), p1 = cellParaIndexOf(end);
    for (let p = p0; p <= p1; p++) {
      const pj = JSON.stringify(path.map((e, i) => (i === path.length - 1 ? { ...e, cellParaIndex: p } : e)));
      const from = p === p0 ? start.charOffset : 0;
      const to = p === p1 ? end.charOffset : wasm.getCellParagraphLengthByPath(sec, start.parentParaIndex, pj);
      if (to > from) parts.push(wasm.getTextInCellByPath(sec, start.parentParaIndex, pj, from, to - from));
    }
  } else {
    for (let s = sec; s <= end.sectionIndex; s++) {
      const p0 = s === sec ? start.paragraphIndex : 0;
      const p1 = s === end.sectionIndex ? end.paragraphIndex : wasm.getParagraphCount(s) - 1;
      for (let p = p0; p <= p1; p++) {
        const from = s === sec && p === p0 ? start.charOffset : 0;
        const to = s === end.sectionIndex && p === p1 ? end.charOffset : wasm.getParagraphLength(s, p);
        if (to > from) parts.push(wasm.getTextRange(s, p, from, to - from));
      }
    }
  }
  return parts.join('');
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

  // 쪽을 넘길 때도 선택 사각형을 다시 그리므로, 선택 양 끝이 그대로면 다시 세지 않는다
  let queued = false;
  let lastKey = '';
  const update = () => {
    queued = false;
    const ih = getInputHandler();
    const sel = ih?.getSelection?.();
    const key = sel ? JSON.stringify([sel.start, sel.end], (k, v) => (k === 'cursorRect' ? undefined : v)) : '';
    if (key === lastKey) return;
    lastKey = key;
    let text = null;
    try { text = sel ? selectedText(ih) : null; } catch { text = null; }
    const show = !!text;
    label.hidden = divider.hidden = !show;
    if (show) {
      const [all, solid] = countText(text);
      label.textContent = `${all.toLocaleString()}글자(공란 제외 ${solid.toLocaleString()}글자)`;
    }
  };
  const schedule = () => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(update);
  };
  for (const name of ['render', 'clear']) {
    const orig = SelectionRenderer.prototype[name];
    SelectionRenderer.prototype[name] = function (...args) {
      const r = orig.apply(this, args);
      schedule();
      return r;
    };
  }
}
