// ==== find ====
  const updates: LocalResizeUpdate[] = [];
  const processedTargets = new Set<number>();
  const processedNeighbors = new Set<number>();
  const laneStart = isHoriz ? range.startRow : range.startCol;
  const laneEnd = isHoriz ? range.endRow : range.endCol;
  const edge = isHoriz ? range.endCol : range.endRow;
  for (let lane = laneStart; lane <= laneEnd; lane++) {
    const target = cells.find(b =>
      axisStart(b, isHoriz) <= edge && edge <= axisEnd(b, isHoriz) && crossContains(b, isHoriz, lane));
    if (!target || processedTargets.has(target.cellIdx)) continue;
    const neighborAxis = axisEnd(target, isHoriz) + 1;
    const neighbor = cells.find(b => axisStart(b, isHoriz) === neighborAxis && crossContains(b, isHoriz, lane));
    if (!target || !neighbor) continue; // 마지막 칸/줄 — 이웃 없음
    if (cellSizeHwp(target, isHoriz) + delta < RESIZE_MIN_CELL_HWP) continue;
    if (cellSizeHwp(neighbor, isHoriz) - delta < RESIZE_MIN_CELL_HWP) continue;
    updates.push(sizeUpdate(target.cellIdx, isHoriz, delta, cellSizeHwp(target, isHoriz) + delta));
    processedTargets.add(target.cellIdx);
    if (!processedNeighbors.has(neighbor.cellIdx)) {
      updates.push(sizeUpdate(neighbor.cellIdx, isHoriz, -delta, cellSizeHwp(neighbor, isHoriz) - delta));
      processedNeighbors.add(neighbor.cellIdx);
    }
  }
  return updates;
// ==== replace ====
  // [claude-hwpx boundary-merged] 병합 칸은 여러 줄에 걸친다. 목표 칸을 첫 줄에서만 처리하고 나머지 줄을 건너뛰면
  // 그 줄의 이웃 칸이 줄지 않아 표가 뒤틀린다(2026-09-27 실측, 여러 줄 병합 칸이 있는 첫 칸을 Shift+왼쪽).
  // 줄마다 짝을 모은 뒤 목표와 이웃을 한 번씩 바꾸고, 하나라도 최소 크기에 걸리면 아무것도 바꾸지 않는다.
  const updates: LocalResizeUpdate[] = [];
  const laneStart = isHoriz ? range.startRow : range.startCol;
  const laneEnd = isHoriz ? range.endRow : range.endCol;
  const edge = isHoriz ? range.endCol : range.endRow;
  const targets = new Map<number, CellBbox>();
  const neighbors = new Map<number, CellBbox>();
  for (let lane = laneStart; lane <= laneEnd; lane++) {
    const target = cells.find(b =>
      axisStart(b, isHoriz) <= edge && edge <= axisEnd(b, isHoriz) && crossContains(b, isHoriz, lane));
    if (!target) continue;
    const neighborAxis = axisEnd(target, isHoriz) + 1;
    const neighbor = cells.find(b => axisStart(b, isHoriz) === neighborAxis && crossContains(b, isHoriz, lane));
    if (!neighbor) continue; // 마지막 칸/줄 — 이웃 없음
    targets.set(target.cellIdx, target);
    neighbors.set(neighbor.cellIdx, neighbor);
  }
  for (const t of targets.values()) if (cellSizeHwp(t, isHoriz) + delta < RESIZE_MIN_CELL_HWP) return [];
  for (const n of neighbors.values()) if (cellSizeHwp(n, isHoriz) - delta < RESIZE_MIN_CELL_HWP) return [];
  // 고른 칸이 경계의 모든 줄을 덮으면 경계 전체를 옮기는 것이다. 마우스 끌기처럼 폭 증감만 보낸다.
  // 부분 조절(localResize)은 줄마다 그 줄에서 시작하는 칸 폭만 쌓아, 병합 칸이 시작하지 않는 줄의 칸이
  // 왼쪽 끝으로 붙는다.
  const lastLane = Math.max(...cells.map(b => (isHoriz ? b.row + b.rowSpan : b.col + b.colSpan) - 1));
  if (laneStart === 0 && laneEnd >= lastLane) {
    const plain = (b: CellBbox, d: number): LocalResizeUpdate =>
      isHoriz ? { cellIdx: b.cellIdx, widthDelta: d } : { cellIdx: b.cellIdx, heightDelta: d };
    return [...[...targets.values()].map(t => plain(t, delta)), ...[...neighbors.values()].map(n => plain(n, -delta))];
  }
  for (const t of targets.values()) updates.push(sizeUpdate(t.cellIdx, isHoriz, delta, cellSizeHwp(t, isHoriz) + delta));
  for (const n of neighbors.values()) updates.push(sizeUpdate(n.cellIdx, isHoriz, -delta, cellSizeHwp(n, isHoriz) - delta));
  return updates;
