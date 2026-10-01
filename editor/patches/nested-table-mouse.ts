// ==== find ====
            const bboxes = this.wasm.getTableCellBboxes(ctx.sec, ctx.ppi, ctx.ci, pageIdx);
            cacheTableCellBboxes(this, ctx, pageIdx, bboxes);
// ==== replace ====
            // [claude-hwpx nested-table-mouse] 표 속 표 칸을 고른 상태면 그 표의 칸 상자로 경계를 잰다(평면 조회는 바깥 표)
            const nestedPath = (ctx.cellPath?.length ?? 0) > 1 ? ctx.cellPath : undefined;
            const bboxes = nestedPath
              ? this.wasm.getTableCellBboxesByPath(ctx.sec, ctx.ppi, JSON.stringify(nestedPath))
              : this.wasm.getTableCellBboxes(ctx.sec, ctx.ppi, ctx.ci, pageIdx);
            cacheTableCellBboxes(this, nestedPath ? { sec: ctx.sec, ppi: ctx.ppi, ci: ctx.ci, path: nestedPath } : ctx, pageIdx, bboxes);
// ==== next ====
      if (this.isTableBorderClick(pageIdx, pageX, pageY, hit.sectionIndex, hit.parentParaIndex, hit.controlIndex)) {
        this.cursor.clearSelection();
        this.cursor.moveToHit(hit); // 셀 위치로 이동 (유효한 렌더링 위치)
        this.cursor.enterTableObjectSelectionDirect(hit.sectionIndex, hit.parentParaIndex, hit.controlIndex);
// ==== replace ====
      // 칸 경로가 표 속 표 안이면 안쪽 표의 바깥 테두리를 먼저 본다
      const nestedPath = Array.isArray(hit.cellPath) && hit.cellPath.length > 1 ? hit.cellPath : undefined;
      const nestedBorder = nestedPath !== undefined
        && this.isNestedTableBorderClick(pageIdx, pageX, pageY, hit.sectionIndex, hit.parentParaIndex, nestedPath);
      if (nestedBorder || this.isTableBorderClick(pageIdx, pageX, pageY, hit.sectionIndex, hit.parentParaIndex, hit.controlIndex)) {
        this.cursor.clearSelection();
        this.cursor.moveToHit(hit); // 셀 위치로 이동 (유효한 렌더링 위치)
        this.cursor.enterTableObjectSelectionDirect(hit.sectionIndex, hit.parentParaIndex, hit.controlIndex, nestedBorder ? nestedPath : undefined);
// ==== next ====
  let tableRef: { sec: number; ppi: number; ci: number } | null = null;
  let tableHit: any = null;
  try {
    const hit = this.wasm.hitTest(pageIdx, pageX, pageY);
    if (hit.parentParaIndex !== undefined && hit.controlIndex !== undefined && !hit.isTextBox) {
      tableHit = hit;
      tableRef = { sec: hit.sectionIndex, ppi: hit.parentParaIndex, ci: hit.controlIndex };
    }
// ==== replace ====
  let tableRef: { sec: number; ppi: number; ci: number; path?: any[] } | null = null;
  let tableHit: any = null;
  try {
    const hit = this.wasm.hitTest(pageIdx, pageX, pageY);
    if (hit.parentParaIndex !== undefined && hit.controlIndex !== undefined && !hit.isTextBox) {
      tableHit = hit;
      // 칸 경로를 함께 싣는다 — 없으면 표 속 표 위에서도 바깥 표 괘선만 캐시에 들어왔다
      tableRef = {
        sec: hit.sectionIndex, ppi: hit.parentParaIndex, ci: hit.controlIndex,
        path: Array.isArray(hit.cellPath) ? hit.cellPath : undefined,
      };
    }
// ==== next ====
  // 해당 페이지의 셀만 필터
  const pageBboxes = bboxes.filter((b: any) => b.pageIndex === pageIdx);
// ==== replace ====
  // 해당 페이지의 셀만 필터
  let pageBboxes = bboxes.filter((b: any) => b.pageIndex === pageIdx);
// ==== next ====
  // 경계선 감지
  const edge = this.tableResizeRenderer.hitTestBorder(pageX, pageY, pageBboxes);
  if (edge) {
// ==== replace ====
  // 경계선 감지
  let edge = this.tableResizeRenderer.hitTestBorder(pageX, pageY, pageBboxes);
  // 표 속 표 테두리의 바깥쪽 몇 px 은 hitTest 가 바깥 칸을 돌려줘 안쪽 표 테두리를 못 잡았다(바깥에서 다가가면 커서가 안 바뀜).
  // 근처에 다른 표의 테두리가 있을 때만 둘레를 찔러 더 깊은 칸이 나오면 그 표의 칸 상자로 판정하고 캐시에 둔다(누르기가 캐시를 쓴다)
  if (!edge && tableHit) {
    const near = (r: any) => Math.min(Math.abs(pageX - r.x), Math.abs(pageX - r.x - r.w), Math.abs(pageY - r.y), Math.abs(pageY - r.y - r.h)) <= 5
      && pageX >= r.x - 5 && pageX <= r.x + r.w + 5 && pageY >= r.y - 5 && pageY <= r.y + r.h + 5;
    let layout: any = null;
    try { layout = this.wasm.getPageControlLayout(pageIdx); } catch { /* 배치 조회 실패면 찔러 보지 않는다 */ }
    if ((layout?.controls ?? []).some((c: any) => c.type === 'table' && near(c))) {
      const depth = tableHit.cellPath?.length ?? 0;
      for (const [dx, dy] of [[0, -4], [0, 4], [-4, 0], [4, 0]]) {
        let h: any = null;
        try { h = this.wasm.hitTest(pageIdx, pageX + dx, pageY + dy); } catch { continue; }
        if (!Array.isArray(h?.cellPath) || h.cellPath.length <= depth || h.isTextBox
          || h.sectionIndex !== tableHit.sectionIndex || h.parentParaIndex !== tableHit.parentParaIndex) continue;
        let nb: any[] = [];
        try { nb = this.wasm.getTableCellBboxesByPath(h.sectionIndex, h.parentParaIndex, JSON.stringify(h.cellPath)); } catch { continue; }
        const npb = nb.filter((b: any) => b.pageIndex === pageIdx);
        const ne = npb.length > 0 ? this.tableResizeRenderer.hitTestBorder(pageX, pageY, npb) : null;
        if (!ne) continue;
        cacheTableCellBboxes(this, { sec: h.sectionIndex, ppi: h.parentParaIndex, ci: h.controlIndex, path: h.cellPath }, pageIdx, nb);
        edge = ne;
        pageBboxes = npb;
        break;
      }
    }
  }
  if (edge) {