// ==== find ====
import { showToast } from '@/ui/toast';
// ==== replace ====
import { showToast } from '@/ui/toast';
import { updateDropLine, clearDropLine, applyDrop, isSoleControlPara } from '@/plugin/move-drop';
// ==== next ====
export function updatePictureMoveDrag(this: any, e: MouseEvent): void {
  if (!this.pictureMoveState) return;
// ==== replace ====
export function updatePictureMoveDrag(this: any, e: MouseEvent): void {
  if (!this.pictureMoveState) return;
  // [claude-hwpx move-drop-line] 흐름을 차지하는 본문 그림(글자처럼 취급, 자리차지)은 끄는 동안 놓일 자리만 푸른 선으로
  // 보여 주고 놓을 때 옮긴다. 떠 있는 그림(글 앞, 글 뒤, 어울림)과 여러 개 선택, 칸 안 그림은 종전처럼 자유롭게 움직인다
  if (this.pictureMoveState.claudeFlow === undefined) {
    const s = this.pictureMoveState;
    let flow = false;
    if (!s.multiRefs && s.ref && s.ref.type === 'image' && !s.ref.cellPath?.length && !s.ref.headerFooter) {
      try {
        const pr = getObjectProperties.call(this, s.ref);
        flow = !!pr.treatAsChar || pr.textWrap === 'TopAndBottom';
      } catch {
        flow = false;
      }
    }
    s.claudeFlow = flow;
  }
  if (this.pictureMoveState.claudeFlow) {
    const r = this.pictureMoveState.ref;
    this.pictureMoveState.claudeDrop = updateDropLine(this, e, r.sec, r.ppi, isSoleControlPara(this, r.sec, r.ppi));
    return;
  }
// ==== next ====
export function finishPictureMoveDrag(this: any): void {
  if (this.pictureMoveState) {
// ==== replace ====
export function finishPictureMoveDrag(this: any): void {
  // [claude-hwpx move-drop-line] 흐름 그림은 놓을 때 그 문단 자리로 옮긴다(되돌리기 한 번)
  if (this.pictureMoveState?.claudeFlow) {
    clearDropLine(this);
    const s = this.pictureMoveState;
    if (s.claudeDrop) {
      const moved = applyDrop(this, s.ref.sec, s.ref.ppi, s.ref.ci, s.claudeDrop.dst);
      if (moved) {
        this.cursor.enterPictureObjectSelectionDirect?.(s.ref.sec, moved.ppi, moved.ci, 'image');
        this.renderPictureObjectSelection?.();
      }
    }
    s.totalDeltaH = 0;
    s.totalDeltaV = 0;
  }
  if (this.pictureMoveState) {
