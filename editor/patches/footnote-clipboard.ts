// ==== find ====
DeleteTextInFootnoteCommand, MergeParagraphInFootnoteCommand, cellParaIndexOf } from './command';
// ==== replace ====
DeleteTextInFootnoteCommand, MergeParagraphInFootnoteCommand, InsertTextInFootnoteCommand, cellParaIndexOf } from './command';
// ==== next ====
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
      e.preventDefault();
      const delta = e.key === 'ArrowLeft' ? -1 : 1;
      this.cursor.moveHorizontalInFn(delta);
// ==== replace ====
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
      e.preventDefault();
      const delta = e.key === 'ArrowLeft' ? -1 : 1;
      // [claude-hwpx footnote-clipboard] Shift+방향키로 각주 안 글을 고른다(끌어 고르기와 같은 fnAnchor)
      if (e.shiftKey) this.cursor.setFnAnchor();
      else this.cursor.clearSelection();
      this.cursor.moveHorizontalInFn(delta);
// ==== next ====
    if ((e.key === 'Home' || e.key === 'End') && !e.ctrlKey && !e.metaKey && !e.altKey) {
      e.preventDefault();
      this.cursor.moveToParagraphEdgeInFn(e.key === 'Home' ? -1 : 1);
// ==== replace ====
    if ((e.key === 'Home' || e.key === 'End') && !e.ctrlKey && !e.metaKey && !e.altKey) {
      e.preventDefault();
      // [claude-hwpx footnote-clipboard] Shift+Home/End 는 고르기를 늘리고, Shift 없이 누르면 고른 범위를 푼다
      if (e.shiftKey) this.cursor.setFnAnchor();
      else this.cursor.clearSelection();
      this.cursor.moveToParagraphEdgeInFn(e.key === 'Home' ? -1 : 1);
// ==== next ====
export function onCopy(this: any, e: ClipboardEvent): void {
  if (!this.active) return;
// ==== replace ====
// [claude-hwpx footnote-clipboard] 각주 편집 중 복사, 잘라내기, 붙여넣기(사용자 보고 2026-10-18: 각주에 캐럿이 있으면 Ctrl+C, V 가
// 먹지 않았다). 복사는 본문 선택(anchor)만 보고 아무것도 하지 않았고, 붙여넣기는 본문 좌표로 들어갔다. 각주 안은 평문으로 주고받는다
function claudeFnTarget(this: any) {
  return {
    sectionIdx: this.cursor.fnSectionIdx, paraIdx: this.cursor.fnParaIdx, controlIdx: this.cursor.fnControlIdx,
    footnoteIndex: this.cursor.fnFootnoteIndex, pageNum: this.cursor.fnPageNum,
  };
}

function claudeFnSelectedText(this: any): string {
  const sel = this.cursor.getFootnoteSelectionOrdered();
  if (!sel) return '';
  const info = this.wasm.getFootnoteInfo(this.cursor.fnSectionIdx, this.cursor.fnParaIdx, this.cursor.fnControlIdx);
  const parts: string[] = [];
  for (let p = sel.start.fnParaIdx; p <= sel.end.fnParaIdx; p++) {
    const t: string = info.texts?.[p] ?? '';
    const a = p === sel.start.fnParaIdx ? sel.start.charOffset : 0;
    const b = p === sel.end.fnParaIdx ? sel.end.charOffset : t.length;
    parts.push(t.slice(a, b));
  }
  return parts.join('\n');
}

/** 각주 안 고른 범위를 지운다(여러 문단이면 끝 문단부터 지우고 문단을 합친다). 빈 범위면 풀기만 하고 false */
export function claudeFnDeleteSelection(this: any): boolean {
  const sel = this.cursor.getFootnoteSelectionOrdered();
  if (!sel) return false;
  const { start, end } = sel;
  this.cursor.clearSelection();
  if (start.fnParaIdx === end.fnParaIdx && end.charOffset <= start.charOffset) return false;
  const target = claudeFnTarget.call(this);
  const info = this.wasm.getFootnoteInfo(target.sectionIdx, target.paraIdx, target.controlIdx);
  const del = (p: number, off: number, n: number, undoCaret: number) => {
    if (n <= 0) return;
    const res = this.wasm.deleteTextInFootnote(target.sectionIdx, target.paraIdx, target.controlIdx, p, off, n);
    if (res.deletedText) {
      this.executeOperation({ kind: 'record', command: new DeleteTextInFootnoteCommand(target, p, off, res.deletedText, undoCaret) });
    }
  };
  if (start.fnParaIdx === end.fnParaIdx) {
    del(start.fnParaIdx, start.charOffset, end.charOffset - start.charOffset, end.charOffset);
  } else {
    del(end.fnParaIdx, 0, end.charOffset, end.charOffset);
    for (let p = end.fnParaIdx - 1; p > start.fnParaIdx; p--) del(p, 0, (info.texts?.[p] ?? '').length, 0);
    const startLen = (info.texts?.[start.fnParaIdx] ?? '').length;
    del(start.fnParaIdx, start.charOffset, startLen - start.charOffset, start.charOffset);
    for (let p = end.fnParaIdx; p > start.fnParaIdx; p--) {
      const result = this.wasm.mergeParagraphInFootnote(target.sectionIdx, target.paraIdx, target.controlIdx, p);
      this.executeOperation({ kind: 'record', command: new MergeParagraphInFootnoteCommand(target, p, result.fnParaIndex, result.charOffset, p, 0, result.removedParaMeta) });
    }
  }
  this.cursor.setFnCursorPosition(start.fnParaIdx, start.charOffset);
  this.afterEdit();
  return true;
}

function claudeFnInsertText(this: any, text: string): void {
  const target = claudeFnTarget.call(this);
  const innerParaIdx = this.cursor.fnInnerParaIdx;
  const charOffset = this.cursor.fnCharOffset;
  this.wasm.insertTextInFootnote(target.sectionIdx, target.paraIdx, target.controlIdx, innerParaIdx, charOffset, text);
  this.executeOperation({ kind: 'record', command: new InsertTextInFootnoteCommand(target, innerParaIdx, charOffset, text) });
  this.cursor.setFnCursorPosition(innerParaIdx, charOffset + text.length);
  this.afterEdit();
}

export function onCopy(this: any, e: ClipboardEvent): void {
  if (!this.active) return;
  if (this.cursor.isInFootnote()) {
    const t = claudeFnSelectedText.call(this);
    if (t) {
      e.preventDefault();
      e.clipboardData?.setData('text/plain', t);
    }
    return;
  }
// ==== next ====
export function onCut(this: any, e: ClipboardEvent): void {
  if (!this.active) return;
  if (this.isFormMode?.()) {
    e.preventDefault();
    return;
  }
// ==== replace ====
export function onCut(this: any, e: ClipboardEvent): void {
  if (!this.active) return;
  if (this.isFormMode?.()) {
    e.preventDefault();
    return;
  }
  // [claude-hwpx footnote-clipboard] 각주 안 잘라내기 = 평문 복사 + 한 문단 안 선택 지우기
  if (this.cursor.isInFootnote()) {
    const t = claudeFnSelectedText.call(this);
    e.preventDefault();
    if (t) {
      e.clipboardData?.setData('text/plain', t);
      claudeFnDeleteSelection.call(this);
    }
    return;
  }
// ==== next ====
        operationType: 'pastePlainTextInHeaderFooter',
        allowCollapsed: true,
      });
    }
    return;
  }
// ==== replace ====
        operationType: 'pastePlainTextInHeaderFooter',
        allowCollapsed: true,
      });
    }
    return;
  }
  // [claude-hwpx footnote-clipboard] 각주 안 붙여넣기는 평문을 각주 캐럿 자리에 넣는다(줄바꿈은 빈칸, 각주 안 문단 나누기는 Enter)
  if (this.cursor.isInFootnote()) {
    if (text) {
      claudeFnDeleteSelection.call(this);
      claudeFnInsertText.call(this, text.replace(/\r?\n/g, ' '));
    }
    return;
  }
// ==== next ====
    // Enter → 각주 내 문단 분할
// ==== replace ====
    // [claude-hwpx footnote-clipboard] 위아래 방향키 → 각주 안 윗줄, 아랫줄(같은 가로 위치). Shift 면 고르기를 늘린다
    if ((e.key === 'ArrowUp' || e.key === 'ArrowDown') && !e.ctrlKey && !e.metaKey && !e.altKey) {
      e.preventDefault();
      const r = this.cursor.getRect();
      if (r) {
        const y = e.key === 'ArrowUp' ? r.y - r.height * 0.5 : r.y + r.height * 1.5;
        try {
          const hit = this.wasm.hitTestInFootnote(r.pageIndex, r.x, y);
          if (hit.hit && hit.footnoteIndex === this.cursor.fnFootnoteIndex && hit.fnParaIndex !== undefined && hit.charOffset !== undefined) {
            if (e.shiftKey) this.cursor.setFnAnchor();
            else this.cursor.clearSelection();
            this.cursor.setFnCursorPosition(hit.fnParaIndex, hit.charOffset);
          }
        } catch { /* 각주 밖이면 움직이지 않는다 */ }
      }
      this.updateCaret();
      return;
    }

    // Enter → 각주 내 문단 분할
// ==== next ====
    if (e.key === 'Backspace' || e.key === 'Delete') {
      e.preventDefault();
      const target = { sectionIdx: this.cursor.fnSectionIdx,
// ==== replace ====
    if (e.key === 'Backspace' || e.key === 'Delete') {
      e.preventDefault();
      // [claude-hwpx footnote-clipboard] 고른 범위가 있으면 그 범위를 지운다(한 글자만 지우던 문제)
      if (claudeFnDeleteSelection.call(this)) return;
      const target = { sectionIdx: this.cursor.fnSectionIdx,
// ==== next ====
export function handleSelectAll(this: any): void {
// ==== replace ====
export function handleSelectAll(this: any): void {
  // [claude-hwpx footnote-clipboard] 각주 편집 중 Ctrl+A 는 그 각주 글 전체를 고른다(본문 전체를 고르던 문제)
  if (this.cursor.isInFootnote()) {
    try {
      const info = this.wasm.getFootnoteInfo(this.cursor.fnSectionIdx, this.cursor.fnParaIdx, this.cursor.fnControlIdx);
      const last = Math.max(0, (info.paraCount ?? 1) - 1);
      this.cursor.clearSelection();
      this.cursor.setFnCursorPosition(0, 0);
      this.cursor.setFnAnchor();
      this.cursor.setFnCursorPosition(last, (info.texts?.[last] ?? '').length);
    } catch { /* 각주 정보를 못 얻으면 그대로 둔다 */ }
    this.updateCaret();
    return;
  }
