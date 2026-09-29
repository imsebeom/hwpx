// ==== find ====
    this.bodyPosSelect = this.selectEl([
      ['Both', '양쪽'], ['Left', '왼쪽'], ['Right', '오른쪽'],
      ['Larger', '큰 쪽'], ['Smaller', '작은 쪽'],
    ]);
    this.bodyPosSelect.disabled = true;
// ==== replace ====
    // [claude-hwpx wrap-text-flow] 본문 위치를 고를 수 있게 한다(HWPX textFlow 네 값, 「작은 쪽」은 없는 값이라 뺐다).
    // 어울림 그림일 때만 켠다 — 엔진 패치 wrap-text-flow-props 가 textFlow 를 주고받는다
    this.bodyPosSelect = this.selectEl([
      ['BothSides', '양쪽'], ['LeftOnly', '왼쪽'], ['RightOnly', '오른쪽'], ['LargestOnly', '큰 쪽'],
    ]);
    this.bodyPosSelect.disabled = true;
// ==== next ====
    this.selectWrap(this.wrapValues.indexOf(this.props.textWrap));
// ==== replace ====
    this.bodyPosSelect.value = (this.props as { textFlow?: string }).textFlow ?? 'BothSides';
    this.selectWrap(this.wrapValues.indexOf(this.props.textWrap));
// ==== next ====
  private selectWrap(idx: number): void {
    this.wrapBtns.forEach((b, i) => b.classList.toggle('active', i === idx));
// ==== replace ====
  private selectWrap(idx: number): void {
    this.wrapBtns.forEach((b, i) => b.classList.toggle('active', i === idx));
    if (this.bodyPosSelect) {
      this.bodyPosSelect.disabled = this.objectType !== 'image'
        || (this.props as { textFlow?: string } | null)?.textFlow === undefined
        || this.wrapValues[idx] !== 'Square';
    }
// ==== next ====
    if (Object.keys(patch).length > 0) this.applyPropertyPatch(patch);
    this.hide();
// ==== replace ====
    const textFlow = (this.props as { textFlow?: string }).textFlow;
    if (!this.bodyPosSelect.disabled && textFlow !== undefined && this.bodyPosSelect.value !== textFlow) {
      (patch as Record<string, unknown>).textFlow = this.bodyPosSelect.value;
    }
    if (Object.keys(patch).length > 0) this.applyPropertyPatch(patch);
    this.hide();
