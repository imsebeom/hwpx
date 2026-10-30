// ==== find ====
  private getCursorRectOnVisualLine(lineIndex: number, atEnd: boolean): CursorRect | null {
    const pos = this.position;
    try {
// ==== replace ====
  private getCursorRectOnVisualLine(lineIndex: number, atEnd: boolean): CursorRect | null {
    const pos = this.position;
    // [claude-hwpx nested-line-caret] 줄 조회는 평평한 좌표만 받아 표 속 표에서는 바깥 칸의 다른 문단을 집는다. 경로 기반 계산(updateRect)으로 넘긴다
    if ((pos.cellPath?.length ?? 0) > 1) return null;
    try {
