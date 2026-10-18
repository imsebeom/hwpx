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

/** 한 문단 안의 각주 선택을 지운다. 문단을 넘는 선택은 지우지 않는다(복사만 된다). 지웠으면 true */
function claudeFnDeleteSelection(this: any): boolean {
  const sel = this.cursor.getFootnoteSelectionOrdered();
  if (!sel || sel.start.fnParaIdx !== sel.end.fnParaIdx) return false;
  const n = sel.end.charOffset - sel.start.charOffset;
  this.cursor.clearSelection();
  if (n <= 0) return true;
  const target = claudeFnTarget.call(this);
  const res = this.wasm.deleteTextInFootnote(target.sectionIdx, target.paraIdx, target.controlIdx, sel.start.fnParaIdx, sel.start.charOffset, n);
  if (res.deletedText) {
    this.executeOperation({ kind: 'record', command: new DeleteTextInFootnoteCommand(target, sel.start.fnParaIdx, sel.start.charOffset, res.deletedText, sel.end.charOffset) });
  }
  this.cursor.setFnCursorPosition(sel.start.fnParaIdx, sel.start.charOffset);
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
