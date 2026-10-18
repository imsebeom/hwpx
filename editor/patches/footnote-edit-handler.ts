// ==== find ====
  private deleteSelection(options?: { deferRecord?: boolean }): void {
// ==== replace ====
  private deleteSelection(options?: { deferRecord?: boolean }): void {
    // [claude-hwpx footnote-edit-handler] 각주 편집 중에는 각주 안 고른 범위를 지운다(글자 입력, 조합 시작이 이 함수를 부른다)
    if (this.cursor.isInFootnote()) {
      _keyboard.claudeFnDeleteSelection.call(this);
      return;
    }
