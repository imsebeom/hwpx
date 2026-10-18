// ==== find ====
      const fnOff = this.cursor.fnCharOffset;
      if (e.key === 'Backspace') {
        if (fnOff > 0) {
// ==== replace ====
      const fnOff = this.cursor.fnCharOffset;
      if (e.key === 'Backspace') {
        // [claude-hwpx fn-number-floor-keyboard] 첫 문단 글 맨 앞(번호 바로 뒤)에서는 번호 둘레 빈칸을 지우지 않는다
        if (fnOff > this.cursor.fnMinOffset(innerParaIdx)) {
