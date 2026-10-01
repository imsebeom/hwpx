// ==== find ====
    s.claudeFlow = flow;
  }
// ==== replace ====
    s.claudeFlow = flow;
    // [claude-hwpx cell-pic-move] 칸(표 속 표 칸 포함) 안 글자처럼 취급 그림은 위치 오프셋이 뜻이 없어 끌어도 아무 일이 없었다.
    // 끄는 동안 놓일 글자 자리에 푸른 세로선을 보여 주고, 놓으면 그 자리로 잘라 붙인다(되돌리기 한 번)
    s.claudeCellPic = false;
    if (!s.multiRefs && s.ref && s.ref.type === 'image' && s.ref.cellPath?.length && !s.ref.headerFooter) {
      try {
        s.claudeCellPic = !!getObjectProperties.call(this, s.ref).treatAsChar;
      } catch {
        s.claudeCellPic = false;
      }
    }
  }
  if (this.pictureMoveState.claudeCellPic) {
    this.pictureMoveState.claudeCellDrop = claudeCellPicDropUpdate(this, e);
    return;
  }
// ==== next ====
export function finishPictureMoveDrag(this: any): void {
// ==== replace ====
export function finishPictureMoveDrag(this: any): void {
  if (this.pictureMoveState?.claudeCellPic) {
    const s = this.pictureMoveState;
    const up = this.claudeMouseUpEvent;
    this.claudeMouseUpEvent = null;
    const drop = up ? claudeCellPicDropUpdate(this, up) : s.claudeCellDrop;
    claudeCellPicDropClear(this);
    if (drop) claudeCellPicMove(this, s.ref, drop);
    s.totalDeltaH = 0;
    s.totalDeltaV = 0;
  }
