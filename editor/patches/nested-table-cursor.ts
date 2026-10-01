// ==== find ====
  enterTableObjectSelectionDirect(sec: number, ppi: number, ci: number): void {
    this._tableObjectSelected = true;
    this.selectedTableRef = { sec, ppi, ci };
  }
// ==== replace ====
  enterTableObjectSelectionDirect(sec: number, ppi: number, ci: number, cellPath?: CellPathEntry[]): void {
    this._tableObjectSelected = true;
    // [claude-hwpx nested-table-cursor] 칸 경로(깊이 2 이상)가 오면 표 속 표를 고른다(테두리 클릭, 크기 조절 끝)
    this.selectedTableRef = cellPath && cellPath.length > 1 ? { sec, ppi, ci, cellPath } : { sec, ppi, ci };
  }
