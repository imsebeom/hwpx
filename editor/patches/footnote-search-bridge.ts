// ==== find ====
  replaceAll(query: string, newText: string, caseSensitive: boolean): import('./types').ReplaceAllResult {
// ==== replace ====
  // [claude-hwpx footnote-search-bridge] 각주, 미주 안 매치 목록과 그 하나 바꾸기(엔진 searchNoteText, replaceNoteHit)
  searchNoteText(query: string, caseSensitive: boolean): Array<{ index: number; sec: number; para: number; noteCtrl: number; notePara: number; charOffset: number; length: number; anchorOffset: number; endnote: boolean; cellContext?: any; cellPath?: any }> {
    if (!this.doc || typeof (this.doc as any).searchNoteText !== 'function') return [];
    return JSON.parse((this.doc as any).searchNoteText(query, caseSensitive));
  }

  replaceNoteHit(query: string, newText: string, caseSensitive: boolean, index: number): { ok: boolean; count?: number } {
    if (!this.doc || typeof (this.doc as any).replaceNoteHit !== 'function') return { ok: false };
    return JSON.parse((this.doc as any).replaceNoteHit(query, newText, caseSensitive, index));
  }

  replaceAll(query: string, newText: string, caseSensitive: boolean): import('./types').ReplaceAllResult {
