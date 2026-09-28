// ==== find ====
import { getObjectProperties, setObjectProperties } from './input-handler-picture';
// ==== replace ====
import { getObjectProperties, setObjectProperties } from './input-handler-picture';
import { updateDropLine, clearDropLine, applyDrop, isSoleControlPara } from '@/plugin/move-drop';
// ==== next ====
    if (Math.hypot(dxFromStart, dyFromStart) < threshold) return;
    this.moveDragState.hasMoved = true;
  }
// ==== replace ====
    if (Math.hypot(dxFromStart, dyFromStart) < threshold) return;
    this.moveDragState.hasMoved = true;
  }
  // [claude-hwpx move-drop-line] 끄는 동안은 문서를 바꾸지 않고 놓일 자리만 푸른 선으로 보여 준다(놓을 때 옮긴다)
  {
    const ref = this.moveDragState.tableRef;
    this.moveDragState.claudeDrop = updateDropLine(this, e, ref.sec, ref.ppi, isSoleControlPara(this, ref.sec, ref.ppi));
    return;
  }
// ==== next ====
export function finishMoveDrag(this: any): void {
  const state = this.moveDragState;
// ==== replace ====
export function finishMoveDrag(this: any): void {
  const state = this.moveDragState;
  // [claude-hwpx move-drop-line] 놓을 때 표를 그 문단 자리로 옮긴다(되돌리기 한 번, 문단 관계와 세로 위치를 다시 맞춘다)
  if (state && state.hasMoved) {
    clearDropLine(this);
    const drop = state.claudeDrop;
    if (drop) {
      const ref = state.tableRef;
      const moved = applyDrop(this, ref.sec, ref.ppi, ref.ci, drop.dst);
      if (moved) {
        state.tableRef = { sec: ref.sec, ppi: moved.ppi, ci: moved.ci };
        this.cursor.updateSelectedTableRef(ref.sec, moved.ppi, moved.ci);
        this.renderTableObjectSelection?.();
      }
    }
  }
