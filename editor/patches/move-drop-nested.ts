// [claude-hwpx move-drop-nested] 표 속 표를 끌면 바깥 표가 옮겨지던 것(2026-10-07 사용자 보고). setup.mjs 가 move-drop-*.ts 뒤에 넣는다.
// ==== table ====
// ==== find ====
import { updateDropLine, clearDropLine, applyDrop, isSoleControlPara } from '@/plugin/move-drop';
// ==== replace ====
import { updateDropLine, clearDropLine, applyDrop, isSoleControlPara, updateCellDropLine, applyCellDrop } from '@/plugin/move-drop';
// ==== next ====
  {
    const ref = this.moveDragState.tableRef;
    this.moveDragState.claudeDrop = updateDropLine(this, e, ref.sec, ref.ppi, isSoleControlPara(this, ref.sec, ref.ppi));
    return;
  }
// ==== replace ====
  {
    // [claude-hwpx move-drop-nested] 표 속 표는 같은 칸 안에서만 옮긴다 — 바깥 표 번호로 옮기면 바깥 표가 통째로 옮겨졌다
    const claudeSel = this.cursor.getSelectedTableRef?.();
    if (claudeSel?.cellPath && claudeSel.cellPath.length > 1) {
      this.moveDragState.claudeDrop = null;
      this.moveDragState.claudeCellDrop = updateCellDropLine(this, e, claudeSel);
      return;
    }
    const ref = this.moveDragState.tableRef;
    this.moveDragState.claudeDrop = updateDropLine(this, e, ref.sec, ref.ppi, isSoleControlPara(this, ref.sec, ref.ppi));
    return;
  }
// ==== next ====
    const drop = state.claudeDrop;
    if (drop) {
// ==== replace ====
    // [claude-hwpx move-drop-nested] 표 속 표: 같은 칸의 놓을 자리로 옮기고 옮긴 표를 다시 고른다
    const claudeCellDrop = state.claudeCellDrop;
    const claudeSel = this.cursor.getSelectedTableRef?.();
    if (claudeCellDrop && claudeSel?.cellPath && claudeSel.cellPath.length > 1) {
      const newPath = applyCellDrop(this, claudeSel, claudeCellDrop.dst);
      if (newPath) {
        this.cursor.enterTableObjectSelectionDirect?.(claudeSel.sec, claudeSel.ppi, claudeSel.ci, newPath);
        this.renderTableObjectSelection?.();
      }
    }
    const drop = state.claudeDrop;
    if (drop) {
// ==== mouse ====
// ==== find ====
import { cacheTableCellBboxes, ensureTableCellBboxCache } from './table-bbox-cache';
// ==== replace ====
import { cacheTableCellBboxes, ensureTableCellBboxCache } from './table-bbox-cache';
import { claudeSelectedTableBBox } from '@/plugin/move-drop';
// ==== all ====
const bbox = this.wasm.getTableBBoxAtPage(ref.sec, ref.ppi, ref.ci, pi);
// ==== replace ====
const bbox = claudeSelectedTableBBox(this, ref, pi);
