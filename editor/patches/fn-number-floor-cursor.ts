// ==== find ====
  /** 각주 내 커서 위치를 설정한다. */
  setFnCursorPosition(fnParaIdx: number, charOffset: number): void {
    this._fnInnerParaIdx = fnParaIdx;
    this._fnCharOffset = charOffset;
    this.updateRect();
  }
// ==== replace ====
  /**
   * [claude-hwpx fn-number-floor-cursor] 각주 첫 문단은 빈칸 둘 사이에 번호가 있어 글은 2부터다. 들어갈 때는 2에 놓지만
   * Home, 왼쪽 키, 번호 누르기, Ctrl+A 가 0으로 보내 그 자리에 치면 글이 번호 앞에 붙었다(사용자 보고 2026-10-19 다음 작업).
   */
  fnMinOffset(fnParaIdx: number): number {
    if (fnParaIdx !== 0) return 0;
    try {
      const info = this.wasm.getFootnoteInfo(this._fnSectionIdx, this._fnParaIdx, this._fnControlIdx);
      return (info.texts?.[0] ?? '').startsWith('  ') ? 2 : 0;
    } catch {
      return 0;
    }
  }

  /** 각주 내 커서 위치를 설정한다. */
  setFnCursorPosition(fnParaIdx: number, charOffset: number): void {
    this._fnInnerParaIdx = fnParaIdx;
    this._fnCharOffset = Math.max(charOffset, this.fnMinOffset(fnParaIdx));
    this.updateRect();
  }
// ==== next ====
    if (edge < 0) {
      this._fnCharOffset = 0;
    } else {
      try {
        const info = this.wasm.getFootnoteInfo(
// ==== replace ====
    if (edge < 0) {
      this._fnCharOffset = this.fnMinOffset(this._fnInnerParaIdx);
    } else {
      try {
        const info = this.wasm.getFootnoteInfo(
// ==== next ====
      if (newOffset >= 0 && newOffset <= charCount) {
        this._fnCharOffset = newOffset;
// ==== replace ====
      if (newOffset >= this.fnMinOffset(this._fnInnerParaIdx) && newOffset <= charCount) {
        this._fnCharOffset = newOffset;
