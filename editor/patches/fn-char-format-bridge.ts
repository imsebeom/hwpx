// ==== find ====
  applyCharFormatInHeaderFooter(
    sec: number,
// ==== replace ====
  // [claude-hwpx fn-char-format-bridge] 각주, 미주 글 범위 글자 모양(엔진 fn-char-format-* 와 짝)
  applyCharFormatInFootnote(sec: number, paraIdx: number, controlIdx: number, startFnPara: number, startOffset: number, endFnPara: number, endOffset: number, propsJson: string): string {
    if (!this.doc) throw new Error('문서가 로드되지 않았습니다');
    return (this.doc as any).applyCharFormatInFootnote(sec, paraIdx, controlIdx, startFnPara, startOffset, endFnPara, endOffset, propsJson);
  }

  getCharPropertiesInFootnote(sec: number, paraIdx: number, controlIdx: number, fnParaIdx: number, charOffset: number): CharProperties {
    if (!this.doc) throw new Error('문서가 로드되지 않았습니다');
    return JSON.parse((this.doc as any).getCharPropertiesInFootnote(sec, paraIdx, controlIdx, fnParaIdx, charOffset));
  }

  applyCharFormatInHeaderFooter(
    sec: number,
