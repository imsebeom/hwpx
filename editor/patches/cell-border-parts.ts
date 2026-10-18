// ==== find ====
  private borderEdits: { type: number; width: number; color: string }[] = [
    { type: 1, width: 0, color: '#000000' },
    { type: 1, width: 0, color: '#000000' },
    { type: 1, width: 0, color: '#000000' },
    { type: 1, width: 0, color: '#000000' },
  ];
  private borderApplyImmediateCheck!: HTMLInputElement;
  private borderScopeRadios!: HTMLInputElement[];
// ==== replace ====
  // [claude-hwpx cell-border-parts] 여러 칸 테두리를 한/글처럼 여섯 부분(0 왼쪽, 1 오른쪽, 2 위, 3 아래 바깥 변, 4 안쪽 가로, 5 안쪽 세로)으로
  // 나눠 고친다. 종전에는 네 변 값을 모든 칸에 그대로 보내 「아래」만 바꿔도 칸마다 아래 변이 바뀌어 안쪽 가로선까지 바뀌었고, 손대지 않은
  // 배경과 대각선도 첫 칸 값으로 덮였다(2026-10-18 사용자 보고). 바꾼 부분만 기억해 칸마다 그 칸 자신의 값 위에 덮는다
  private borderEdits: { type: number; width: number; color: string }[] = [
    { type: 1, width: 0, color: '#000000' },
    { type: 1, width: 0, color: '#000000' },
    { type: 1, width: 0, color: '#000000' },
    { type: 1, width: 0, color: '#000000' },
    { type: 1, width: 0, color: '#000000' },
    { type: 1, width: 0, color: '#000000' },
  ];
  private claudeTouched = new Set<number>();
  private claudeBgTouched = false;
  private claudeDiagTouched = false;
  private borderApplyImmediateCheck!: HTMLInputElement;
  private borderScopeRadios!: HTMLInputElement[];
// ==== next ====
    body.appendChild(tabBar);
    body.appendChild(panelContainer);
    this.switchTab(0);
// ==== replace ====
    body.appendChild(tabBar);
    body.appendChild(panelContainer);
    // 배경, 대각선 탭은 사용자가 그 안을 건드렸을 때만 값을 보낸다(안 건드리면 칸마다 제 배경, 대각선 그대로)
    for (const ev of ['input', 'change', 'click']) {
      this.panels[1]?.addEventListener(ev, () => { this.claudeBgTouched = true; });
      this.panels[2]?.addEventListener(ev, () => { this.claudeDiagTouched = true; });
    }
    this.switchTab(0);
// ==== next ====
    const presets = [
      { label: '모두', dirs: [0, 1, 2, 3] },
      { label: '바깥쪽', dirs: [0, 1, 2, 3] },
      { label: '안쪽', dirs: [] as number[] },
    ];
// ==== replace ====
    const presets = [
      { label: '모두', dirs: [0, 1, 2, 3, 4, 5] },
      { label: '바깥쪽', dirs: [0, 1, 2, 3] },
      { label: '안쪽', dirs: [4, 5] },
    ];
// ==== next ====
    previewWrap.appendChild(mkDirBtn('O', 'tcp-dir-all', 4));
    previewWrap.appendChild(mkDirBtn('▲', 'tcp-dir-top', 2));
    previewWrap.appendChild(document.createElement('span'));
// ==== replace ====
    previewWrap.appendChild(mkDirBtn('O', 'tcp-dir-all', -1));
    previewWrap.appendChild(mkDirBtn('▲', 'tcp-dir-top', 2));
    // 안쪽 가로선, 안쪽 세로선 단추(여러 칸을 골랐을 때만)
    const innerBtn = (text: string, title: string, dirIdx: number): HTMLElement => {
      if (!this.claudeMulti()) return document.createElement('span');
      const btn = mkDirBtn(text, 'tcp-dir-inner', dirIdx);
      btn.title = title;
      return btn;
    };
    previewWrap.appendChild(innerBtn('─', '안쪽 가로선', 4));
// ==== next ====
    previewWrap.appendChild(mkDirBtn('▶', 'tcp-dir-right', 1));
    previewWrap.appendChild(document.createElement('span'));
// ==== replace ====
    previewWrap.appendChild(mkDirBtn('▶', 'tcp-dir-right', 1));
    previewWrap.appendChild(innerBtn('│', '안쪽 세로선', 5));
// ==== next ====
    if (dirIdx === 4) {
      this.borderEdits = [val, val, val, val];
    } else {
      this.borderEdits[dirIdx] = val;
    }
  }
// ==== replace ====
    // -1 은 여섯 부분 모두
    const dirs = dirIdx < 0 ? [0, 1, 2, 3, 4, 5] : [dirIdx];
    for (const d of dirs) {
      this.borderEdits[d] = { ...val };
      this.claudeTouched.add(d);
    }
  }

  /** 여러 칸(2칸 이상 범위)을 골랐는가 */
  private claudeMulti(): boolean {
    const r = this.selectionRange;
    return !!r && (r.endRow > r.startRow || r.endCol > r.startCol);
  }
// ==== next ====
    drawLine(2, 98, 118, 98, this.borderEdits[3]);
  }
// ==== replace ====
    drawLine(2, 98, 118, 98, this.borderEdits[3]);
    if (this.claudeMulti()) {
      drawLine(2, 50, 118, 50, this.borderEdits[4]);
      drawLine(60, 2, 60, 98, this.borderEdits[5]);
    }
  }
// ==== next ====
        this.borderEdits[i] = { type: b.type, width: b.width, color: b.color };
      }
    }
    this.updateBorderPreview();
// ==== replace ====
        this.borderEdits[i] = { type: b.type, width: b.width, color: b.color };
      }
    }
    // 안쪽 가로, 세로는 처음 칸의 아래, 오른쪽 변으로 보인다
    this.borderEdits[4] = { ...this.borderEdits[3] };
    this.borderEdits[5] = { ...this.borderEdits[1] };
    this.updateBorderPreview();
// ==== next ====
      if (scope === 'all') {
        const dims = this.wasm.getTableDimensions(sec, ppi, ci);
        const all = Array.from({ length: dims.cellCount }, (_, i) => i);
        return { kind: 'cells', cellIdxes: all };
      }
      if (this.selectionRange) {
        const cellIndices = this.selectedCellIndicesForRange(this.selectionRange);
        return { kind: 'cells', cellIdxes: cellIndices.length > 0 ? cellIndices : [this.cellIdx] };
      }
      return { kind: 'cells', cellIdxes: [this.cellIdx] };
    };
// ==== replace ====
      if (scope === 'all') {
        const dims = this.wasm.getTableDimensions(sec, ppi, ci);
        const all = Array.from({ length: dims.cellCount }, (_, i) => i);
        return claudePerCell(all, { startRow: 0, startCol: 0, endRow: Math.max(0, dims.rowCount - 1), endCol: Math.max(0, dims.colCount - 1) });
      }
      if (this.selectionRange) {
        const cellIndices = this.selectedCellIndicesForRange(this.selectionRange);
        return claudePerCell(cellIndices.length > 0 ? cellIndices : [this.cellIdx], this.selectionRange);
      }
      return claudePerCell([this.cellIdx], null);
    };
// ==== next ====
      this.wasm.runInBatch(() => {
        for (const cellIdx of t.cellIdxes) {
          this.wasm.setCellProperties(sec, ppi, ci, cellIdx, newProps as Partial<CellProperties>);
        }
      });
// ==== replace ====
      this.wasm.runInBatch(() => {
        for (const [k, cellIdx] of t.cellIdxes.entries()) {
          this.wasm.setCellProperties(sec, ppi, ci, cellIdx, (t.propsByCell?.[k] ?? newProps) as Partial<CellProperties>);
        }
      });
// ==== next ====
    // [#5959] 적용 대상을 데이터로 고정한다 — 커맨드 execute 가 다시 읽지 않는다.
    const buildTargets = (): CellBorderFillTarget => {
// ==== replace ====
    // 각 셀마다 적용: 칸마다 네 변이 범위의 바깥 변인지 안쪽 가로, 세로선인지 가려 사용자가 바꾼 부분만 그 칸 자신의 값 위에 덮는다.
    // 테두리 변경은 엔진이 borderLeft 키로 알아보므로 네 변은 늘 보내고(안 바꾼 변은 제 값), 배경과 대각선은 그 탭을 건드렸을 때만 보낸다
    const claudePerCell = (cellIdxes: number[], range: CellRange | null): CellBorderFillTarget => {
      const bboxes = new Map<number, CellBbox>();
      for (const b of this.wasm.getTableCellBboxes(sec, ppi, ci)) if (!bboxes.has(b.cellIdx)) bboxes.set(b.cellIdx, b);
      const sides = ['borderLeft', 'borderRight', 'borderTop', 'borderBottom'] as const;
      const fillKeys = ['fillType', 'fillColor', 'patternColor', 'patternType'];
      const diagKeys = ['diagonalLine', 'diagonalSlash', 'diagonalBackSlash', 'diagonalWidth', 'diagonalColor', 'centerLine'];
      const propsByCell = cellIdxes.map((cellIdx) => {
        const own = this.wasm.getCellOwnProperties(sec, ppi, ci, cellIdx);
        const b = bboxes.get(cellIdx);
        const endRow = b ? b.row + Math.max(1, b.rowSpan) - 1 : 0;
        const endCol = b ? b.col + Math.max(1, b.colSpan) - 1 : 0;
        const roles = b && range
          ? [b.col <= range.startCol ? 0 : 5, endCol >= range.endCol ? 1 : 5, b.row <= range.startRow ? 2 : 4, endRow >= range.endRow ? 3 : 4]
          : [0, 1, 2, 3];
        const p: Record<string, unknown> = { borderFillId: own.borderFillId ?? 0 };
        sides.forEach((key, i) => {
          const o = own[key];
          p[key] = this.claudeTouched.has(roles[i])
            ? this.borderEdits[roles[i]]
            : o ? { type: o.type, width: o.width, color: o.color } : this.borderEdits[i];
        });
        if (this.claudeBgTouched) for (const key of fillKeys) if (key in newProps) p[key] = newProps[key];
        if (this.claudeDiagTouched) for (const key of diagKeys) p[key] = newProps[key];
        return p;
      });
      return { kind: 'cells', cellIdxes, propsByCell };
    };
    // [#5959] 적용 대상을 데이터로 고정한다 — 커맨드 execute 가 다시 읽지 않는다.
    const buildTargets = (): CellBorderFillTarget => {
