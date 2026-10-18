// ==== find ====
  | { kind: 'cells'; cellIdxes: number[] }
// ==== replace ====
  // [claude-hwpx cell-border-parts-cmd] propsByCell: 칸마다 다른 속성(cellIdxes 와 같은 차례). 여러 칸의 바깥 변, 안쪽 가로, 안쪽 세로를
  // 나눠 바꿀 때 칸마다 그 칸 자신의 값 위에 바꾼 부분만 덮은 속성을 넘긴다
  | { kind: 'cells'; cellIdxes: number[]; propsByCell?: Record<string, unknown>[] }
// ==== next ====
          for (const cellIdx of target.cellIdxes) {
            const r = wasm.setCellProperties(
              this.sec, this.ppi, this.ci, cellIdx,
              this.props as Partial<CellProperties>,
            );
// ==== replace ====
          for (const [k, cellIdx] of target.cellIdxes.entries()) {
            const r = wasm.setCellProperties(
              this.sec, this.ppi, this.ci, cellIdx,
              (target.propsByCell?.[k] ?? this.props) as Partial<CellProperties>,
            );
