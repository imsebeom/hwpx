// ==== find ====
                if (!props.treatAsChar || (ref.type === 'image' && !ref.cellPath?.length && !ref.headerFooter)) {
// ==== replace ====
                // [claude-hwpx cell-pic-move-start] 칸 안 글자처럼 취급 그림도 끌기를 시작한다 — 놓을 때 글자 자리로 잘라 붙인다(cell-pic-move)
                if (!props.treatAsChar || (ref.type === 'image' && !ref.headerFooter)) {
// ==== next ====
    this.finishPictureMoveDrag();
// ==== replace ====
    // 끄는 처리는 화면 프레임마다 첫 이동만 써서 마지막 위치가 빠질 수 있다 — 놓은 좌표를 남겨 칸 그림 옮기기가 다시 판정한다
    this.claudeMouseUpEvent = _e;
    this.finishPictureMoveDrag();
