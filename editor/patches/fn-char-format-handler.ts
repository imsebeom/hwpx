// ==== find ====
    // 각주는 아직 전용 범위 API가 없어 예약 자체를 차단한다.
    if (this.cursor.isInFootnote()) return;
// ==== replace ====
    // [claude-hwpx fn-char-format-handler] 각주는 고른 범위에 글자 모양을 입힌다(엔진 fn-char-format-*). 고른 것이 없으면 머리말처럼 아무것도 안 한다
    if (this.cursor.isInFootnote()) {
      const sel = this.cursor.getFootnoteSelectionOrdered?.();
      if (!sel || (sel.start.fnParaIdx === sel.end.fnParaIdx && sel.end.charOffset <= sel.start.charOffset)) return;
      const c = this.cursor;
      const context: EditContext = {
        mode: 'footnote',
        sectionIdx: c.fnSectionIdx,
        paraIdx: c.fnParaIdx,
        controlIdx: c.fnControlIdx,
        footnoteIndex: c.fnFootnoteIndex,
        pageNum: c.fnPageNum,
        innerParaIdx: c.fnInnerParaIdx,
        charOffset: c.fnCharOffset,
      };
      const bodyPosition = c.getPosition();
      this.executeOperation({
        kind: 'snapshot',
        operationType: 'applyCharFormatInFootnote',
        editContext: context,
        editContextAfter: context,
        operation: (wasm: any) => {
          wasm.applyCharFormatInFootnote(
            context.sectionIdx, context.paraIdx, context.controlIdx,
            sel.start.fnParaIdx, sel.start.charOffset, sel.end.fnParaIdx, sel.end.charOffset,
            JSON.stringify(props),
          );
          return { ...bodyPosition };
        },
      });
      return;
    }
// ==== next ====
    const sel = this.getNonEmptySelection();
    const pos = sel ? sel.start : this.cursor.getPosition();
// ==== replace ====
    // [claude-hwpx fn-char-format-handler] 각주는 고른 범위 첫 글자, 없으면 캐럿 앞 글자의 모양(툴바 표시, Ctrl+B 토글 방향)
    if (this.cursor.isInFootnote()) {
      const c = this.cursor;
      const fsel = c.getFootnoteSelectionOrdered?.();
      const nonEmpty = fsel && !(fsel.start.fnParaIdx === fsel.end.fnParaIdx && fsel.end.charOffset <= fsel.start.charOffset);
      const fp = nonEmpty ? fsel.start.fnParaIdx : c.fnInnerParaIdx;
      const off = nonEmpty ? fsel.start.charOffset : Math.max(0, c.fnCharOffset - 1);
      try {
        return this.wasm.getCharPropertiesInFootnote(c.fnSectionIdx, c.fnParaIdx, c.fnControlIdx, fp, off);
      } catch { /* 각주 정보를 못 읽으면 본문 기준으로 */ }
    }
    const sel = this.getNonEmptySelection();
    const pos = sel ? sel.start : this.cursor.getPosition();
