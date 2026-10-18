// ==== find ====
  private currentHit: SearchResult | null = null;
// ==== replace ====
  private currentHit: SearchResult | null = null;
  // [claude-hwpx footnote-search-find] 본문 매치를 한 바퀴 훑으면(또는 없으면) 각주, 미주 안 매치를 차례로 훑는다. noteIdx >= 0 이면 각주 차례
  private noteIdx = -1;
  private noteHit: any = null;
// ==== next ====
    const pos = ih.getCursorPosition();
// ==== replace ====
    const pos = ih.getCursorPosition();

    // [claude-hwpx footnote-search] 각주 차례면 다음(이전) 각주 매치로 가고, 다 훑으면 본문 처음(끝)으로 돌아간다
    if (this.noteIdx >= 0) {
      const notes = this.services.wasm.searchNoteText(query, this.caseSensitiveCheck.checked);
      const next = this.noteIdx + (forward ? 1 : -1);
      if (next >= 0 && next < notes.length) { this.showNoteHit(notes, next); return; }
      this.noteIdx = -1;
      this.noteHit = null;
      const far = forward ? 0 : 0x7fffffff;
      const body = this.services.wasm.searchText(query, far, far, far, forward, this.caseSensitiveCheck.checked, true);
      if (body.found) {
        this.currentHit = body;
        this.navigateToHit(body);
        this.statusLabel.style.color = '#0066cc';
        this.statusLabel.textContent = forward ? '각주까지 찾았습니다. 본문 처음부터 계속합니다.' : '각주까지 찾았습니다. 본문 끝부터 계속합니다.';
        return;
      }
      if (notes.length) { this.showNoteHit(notes, forward ? 0 : notes.length - 1); return; }
    }
// ==== next ====
    if (result.found) {
// ==== replace ====
    // [claude-hwpx footnote-search] 본문 매치가 없거나 한 바퀴 돌았으면 각주, 미주 안을 훑는다
    if (!result.found || result.wrapped) {
      const notes = this.services.wasm.searchNoteText(query, this.caseSensitiveCheck.checked);
      if (notes.length) { this.showNoteHit(notes, forward ? 0 : notes.length - 1); return; }
    }
    if (result.found) {
// ==== next ====
  private navigateToHit(hit: SearchResult): void {
// ==== replace ====
  // [claude-hwpx footnote-search] 각주 매치는 그 각주가 달린 자리(각주 번호)를 고르고 상태 줄에 알린다.
  // 각주 편집 화면은 칸 안 각주를 열지 못해 달린 자리로 간다. 바꾸기는 이 매치 하나를 바꾼다
  private showNoteHit(notes: any[], i: number): void {
    const h = notes[i];
    this.noteIdx = i;
    this.noteHit = h;
    this.currentHit = null;
    this.navigateToHit({ found: true, sec: h.sec, para: h.para, charOffset: h.anchorOffset, length: 1, cellContext: h.cellContext } as SearchResult);
    const kind = h.endnote ? '미주' : '각주';
    this.statusLabel.style.color = '#0066cc';
    this.statusLabel.textContent = `${kind} 안에서 찾음(${i + 1}/${notes.length}). 바꾸기를 누르면 이 ${kind}의 글을 바꿉니다.`;
  }

  private navigateToHit(hit: SearchResult): void {
// ==== next ====
  private doReplace(): void {
// ==== replace ====
  private doReplace(): void {
    // [claude-hwpx footnote-search] 각주 안 매치면 그 매치 하나를 바꾸고 다음 각주 매치로 간다
    if (this.noteIdx >= 0 && this.noteHit) {
      const query = this.queryInput.value;
      const newText = this.replaceInput.value;
      const cs = this.caseSensitiveCheck.checked;
      const index: number = this.noteHit.index;
      const before = this.services.wasm.searchNoteText(query, cs).length;
      let r: { ok: boolean } = { ok: false };
      const ih = this.services.getInputHandler();
      if (ih) {
        ih.executeOperation({ kind: 'snapshot', operationType: 'replaceText', operation: (wasm) => {
          r = wasm.replaceNoteHit(query, newText, cs, index);
          return ih.getCursorPosition();
        }});
      } else {
        r = this.services.wasm.replaceNoteHit(query, newText, cs, index);
        this.services.eventBus.emit('document-changed');
      }
      if (r.ok) {
        const left = this.services.wasm.searchNoteText(query, cs);
        // 바꾼 글이 더 이상 맞지 않으면 같은 번호가 다음 매치, 여전히 맞으면 그다음 번호로 간다
        const nextIdx = left.length < before ? index : index + 1;
        if (nextIdx < left.length) {
          this.showNoteHit(left, nextIdx);
        } else {
          this.noteIdx = left.length - 1;
          this.doSearch(true);
        }
      }
      return;
    }
