// ==== find ====
  getPageFootnoteInfo(pageNum: number, footnoteIndex: number): { ok: boolean; sectionIdx: number; paraIdx: number; controlIdx: number; sourceType: string } | null {
// ==== replace ====
  // [claude-hwpx fn-cell-target-bridge] 표 칸 안 각주 위치를 엔진에 등록하고 각주 함수에 넘길 가짜 컨트롤 번호를 받는다
  registerFootnoteCellTarget(parentPara: number, tableCtrl: number, cellIdx: number, cellPara: number, cellCtrl: number): number | null {
    if (!this.doc || typeof (this.doc as any).registerFootnoteCellTarget !== 'function') return null;
    return (this.doc as any).registerFootnoteCellTarget(parentPara, tableCtrl, cellIdx, cellPara, cellCtrl);
  }

  getPageFootnoteInfo(pageNum: number, footnoteIndex: number): { ok: boolean; sectionIdx: number; paraIdx: number; controlIdx: number; sourceType: string; cellIdx?: number; cellParaIdx?: number; cellControlIdx?: number } | null {
