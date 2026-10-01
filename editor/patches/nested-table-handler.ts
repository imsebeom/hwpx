// ==== find ====
import { isPointNearBoxBorder } from './table-border-hit';
// ==== replace ====
import { isPointNearBoxBorder } from './table-border-hit';
import { isSameNestedTablePath } from './table-bbox-cache'; // [claude-hwpx nested-table-handler]
// ==== next ====
  /** 클릭 좌표가 표 외곽 경계선 위인지 판별한다 (페이지 좌표 기준) */
  private isTableBorderClick(
// ==== replace ====
  /** 클릭 좌표가 칸 경로(깊이 2 이상)가 가리키는 표 속 표의 바깥 테두리 위인가. 칸 상자 합집합으로 판정한다
   *  (getTableBBoxAtPage 는 맨 바깥 표만 돌려준다) */
  isNestedTableBorderClick(
    pageIdx: number,
    pageX: number, pageY: number,
    sec: number, ppi: number,
    cellPath: { controlIndex: number; cellIndex: number; cellParaIndex: number }[],
  ): boolean {
    try {
      const cells = this.wasm.getTableCellBboxesByPath(sec, ppi, JSON.stringify(cellPath))
        .filter((b: { pageIndex: number }) => b.pageIndex === pageIdx);
      if (cells.length === 0) return false;
      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
      for (const c of cells) {
        minX = Math.min(minX, c.x);
        minY = Math.min(minY, c.y);
        maxX = Math.max(maxX, c.x + c.w);
        maxY = Math.max(maxY, c.y + c.h);
      }
      return isPointNearBoxBorder(pageX, pageY, { x: minX, y: minY, width: maxX - minX, height: maxY - minY });
    } catch {
      return false;
    }
  }

  /** 클릭 좌표가 표 외곽 경계선 위인지 판별한다 (페이지 좌표 기준) */
  private isTableBorderClick(
// ==== next ====
      if (hit.parentParaIndex !== ctx.ppi || hit.controlIndex !== ctx.ci) return null;
      if (hit.cellIndex === undefined) return null;
      if (ctx.cellPath && ctx.cellPath.length > 1 && hit.cellPath) {
// ==== replace ====
      if (hit.sectionIndex !== ctx.sec || hit.parentParaIndex !== ctx.ppi || hit.controlIndex !== ctx.ci) return null;
      if (hit.cellIndex === undefined) return null;
      if (ctx.cellPath && ctx.cellPath.length > 1) {
        // 표 속 표에서는 같은 안쪽 표를 가리킬 때만 받는다 — 바깥 칸이나 형제 표 경로로 엉뚱한 칸이 골라졌다
        if (!isSameNestedTablePath(ctx.cellPath, hit.cellPath)) return null;
