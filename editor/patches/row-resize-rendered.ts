// ==== find ====
  const updates = build(bboxes, range, key);
  if (updates.length === 0) return;
// ==== replace ====
  let updates = build(bboxes, range, key);
  if (updates.length === 0) return;
  // [claude-hwpx row-resize-rendered] Ctrl+위/아래는 고른 행을 **그려진 높이**에서 한 단계 바꾼다(한글과 같다).
  // 적힌 칸 높이에 더하면 내용보다 작게 적힌 칸은 늘지 않고, 표 높이와 행 합이 어긋나 모든 행이 비례로 커졌다
  // (2026-09-28). 고른 행에 걸친 칸만 보내고, 엔진에 표 높이를 다시 재라는 표식을 함께 보낸다(엔진 패치 row-resize-th).
  // 여러 쪽에 걸친 표는 행 높이를 쪽 조각으로만 알 수 있어 종전 방식을 쓴다.
  if (operationType === 'resizeCellByKeyboard' && (key === 'ArrowUp' || key === 'ArrowDown')
    && new Set(bboxes.map((b) => b.pageIndex)).size === 1) {
    try {
      const step = key === 'ArrowDown' ? 300 : -300;
      const seen = new Set<number>();
      const out: any[] = [];
      for (const b of bboxes) {
        if (seen.has(b.cellIdx)) continue;
        seen.add(b.cellIdx);
        // 합친 칸도 걸친 고른 행 수만큼 바꾼다 — 빼면 고른 행들의 합이 합친 칸 높이에 묶여 한 행이 줄 때 다른 행이 늘었다
        const overlap = Math.max(0, Math.min(b.row + b.rowSpan - 1, range.endRow) - Math.max(b.row, range.startRow) + 1);
        if (overlap <= 0) continue;
        const declared = this.wasm.getCellProperties(ctx.sec, ctx.ppi, ctx.ci, b.cellIdx).height;
        const d = Math.round(b.h * 75) + step * overlap - declared;
        if (d !== 0) out.push({ cellIdx: b.cellIdx, heightDelta: d });
      }
      if (out.length > 0) {
        // 표 높이는 엔진이 조절 뒤 다시 잰다(내용 최소 높이에 걸린 행을 여기서는 모른다). 값은 표식일 뿐이다
        out.push({ cellIdx: -1, tableHeight: 1 });
        updates = out;
      }
    } catch { /* 종전 방식 */ }
  }
