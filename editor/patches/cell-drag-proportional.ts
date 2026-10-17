// ==== find ====
  const range = inCellSel ? this.cursor.getSelectedCellRange() : null;

  if (state.singleCellTarget) {
// ==== replace ====
  const range = inCellSel ? this.cursor.getSelectedCellRange() : null;
  // [claude-hwpx cell-drag-proportional] 칸 여러 열(행)을 고르고 고른 범위 끝 테두리를 끌면 고른 열(행)이 지금 크기 비율대로 함께 바뀐다(한/글)
  const claudeProportional = !state.singleCellTarget && range
    ? claudeProportionalDragUpdates(this, state, range, deltaHwpUnit)
    : null;

  if (claudeProportional) {
    if (claudeProportional.length === 0) {
      this.cleanupResizeDrag();
      return;
    }
    updates = claudeProportional;
  } else if (state.singleCellTarget) {
// ==== next ====
    shiftResize: shouldResizeSingleCell,
  };

  // mouseup 리스너 등록 (document 레벨)
// ==== replace ====
    shiftResize: shouldResizeSingleCell,
  };
  // [claude-hwpx cell-drag-proportional] 비례 끌기면 끝 열(행) 하나와 이웃의 한도로 끌 범위를 막지 않는다. 줄일 때는 고른 열(행)
  // 모두가 나눠 줄고, 행은 아래 이웃을 줄이지 않는다. 최소 크기는 놓을 때 claudeProportionalDragUpdates 가 지킨다
  const claudeRange = this.cursor.isInCellSelectionMode() ? this.cursor.getSelectedCellRange() : null;
  if (claudeRange && !singleCellTarget
      && claudeProportionalDragUpdates(this, this.resizeDragState, claudeRange, 1) !== null) {
    this.resizeDragState.minResizePos = -Infinity;
    if (edge.type === 'row') this.resizeDragState.maxResizePos = Infinity;
  }

  // mouseup 리스너 등록 (document 레벨)
// ==== next ====
export function cleanupResizeDrag(this: any): void {
// ==== replace ====
/**
 * [claude-hwpx cell-drag-proportional] 칸 선택 중 끌기: 고른 범위가 열(행) 둘 이상이고 끈 테두리가 그 범위의 끝
 * 테두리이면, 늘어난 양을 고른 열(행)의 지금 크기 비율로 나눈다. 열은 종전 끌기처럼 오른쪽 이웃 열을 그만큼 줄여 표
 * 폭을 지킨다(표 끝 테두리면 이웃이 없어 표가 커진다). 행은 이웃을 줄이지 않고 표 높이가 바뀐다 — 아래 행은 글 높이
 * 아래로 줄지 않아, 이웃 한도에 맞추면 끈 양의 일부만 늘었다. 종전에는 끝 열(행)만 바뀌었다(2026-10-17 사용자 요청).
 * 열은 고른 행의 칸만, 행은 그 행의 모든 칸을 바꾼다. 행은 그려진 높이에 더해 보내고 표 높이를 다시 재게 한다
 * (row-resize-rendered 와 같은 방식). 해당하지 않으면 null(종전 처리), 바꿀 것이 없으면 빈 배열.
 */
function claudeProportionalDragUpdates(self: any, state: any, range: any, delta: number): any[] | null {
  const isCol = state.edge.type === 'col';
  const cells: CellBbox[] = [];
  const seen = new Set<number>();
  for (const b of state.bboxes as CellBbox[]) {
    if (seen.has(b.cellIdx)) continue;
    seen.add(b.cellIdx);
    cells.push(b);
  }
  const lo = (b: CellBbox) => (isCol ? b.col : b.row);
  const hi = (b: CellBbox) => lo(b) + (isCol ? b.colSpan : b.rowSpan) - 1;
  const size = (b: CellBbox) => (isCol ? b.w : b.h) * 75;
  const selected = cells.filter(b => cellOverlapsSelectionRange(b, range));
  if (selected.length === 0) return null;
  const s0 = Math.min(...selected.map(lo));
  const s1 = Math.max(...selected.map(hi));
  if (s1 <= s0) return null;
  // 끈 테두리가 고른 범위 끝 테두리인지는 좌표로 본다(경계 번호는 좌표 순번이라 열, 행 번호와 다르다)
  const ends = (state.pageBboxes as CellBbox[]).filter(b => cellOverlapsSelectionRange(b, range) && hi(b) === s1);
  if (!ends.some(b => Math.abs((isCol ? b.x + b.w : b.y + b.h) - state.borderOriginalPos) <= 1)) return null;
  // 행: 여러 쪽에 걸친 표는 행 높이를 쪽 조각으로만 알고, 표 속 표는 표 높이 다시 재기를 받지 않는다 — 종전 처리
  if (!isCol && (new Set(cells.map(b => b.pageIndex)).size > 1 || claudeNestedPath(state.tableRef))) return null;
  // 열은 고른 행에 걸친 칸만 바꾼다
  const cross = (b: CellBbox) => !isCol || (b.row <= range.endRow && b.row + b.rowSpan - 1 >= range.startRow);

  // 고른 열(행)마다 지금 크기. 한 칸짜리 칸에서 읽고, 없으면 합친 칸을 나눠 어림한다
  const lineSize = new Map<number, number>();
  for (let k = s0; k <= s1; k++) {
    const one = cells.find(b => lo(b) === k && hi(b) === k && cross(b));
    const any = one ?? cells.find(b => lo(b) <= k && k <= hi(b) && cross(b));
    if (!any) return null;
    lineSize.set(k, size(any) / (hi(any) - lo(any) + 1));
  }
  const total = [...lineSize.values()].reduce((a, v) => a + v, 0);
  if (total <= 0) return null;
  const neighbors = isCol ? cells.filter(b => lo(b) <= s1 + 1 && s1 + 1 <= hi(b) && cross(b)) : [];

  // 최소 크기: 줄일 때는 고른 열(행)이, 늘릴 때는 이웃이 걸린다
  const MIN = 300;
  let d = delta;
  if (d < 0) for (const v of lineSize.values()) d = Math.max(d, -Math.max(0, v - MIN) * total / v);
  if (d > 0) for (const n of neighbors) d = Math.min(d, Math.max(0, size(n) / (hi(n) - lo(n) + 1) - MIN));
  d = Math.trunc(d);
  if (d === 0) return [];

  const lineDelta = new Map<number, number>();
  let acc = 0;
  for (let k = s0; k <= s1; k++) {
    const v = k === s1 ? d - acc : Math.round(d * (lineSize.get(k) as number) / total);
    acc += v;
    lineDelta.set(k, v);
  }
  if (neighbors.length > 0) lineDelta.set(s1 + 1, -d);

  const out: any[] = [];
  for (const b of cells) {
    if (!cross(b)) continue;
    let cd = 0;
    for (let k = lo(b); k <= hi(b); k++) cd += lineDelta.get(k) ?? 0;
    if (cd === 0) continue;
    if (isCol) {
      out.push({ cellIdx: b.cellIdx, widthDelta: cd });
    } else {
      const declared = claudeCellProps(self.wasm, state.tableRef, b.cellIdx).height;
      const want = Math.max(MIN, Math.round(b.h * 75) + cd);
      if (want !== declared) out.push({ cellIdx: b.cellIdx, heightDelta: want - declared });
    }
  }
  if (!isCol && out.length > 0) out.push({ cellIdx: -1, tableHeight: 1 });
  return out;
}

export function cleanupResizeDrag(this: any): void {
