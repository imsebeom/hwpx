// ==== find ====
    const ref = this.moveDragState.tableRef;
    const result = this.wasm.moveTableOffset(ref.sec, ref.ppi, ref.ci, deltaH, deltaV);
// ==== replace ====
    const ref = this.moveDragState.tableRef;
    // [claude-hwpx table-move-undo] 되돌리기를 정확하게 하려고 처음 움직일 때 문서 상태를 저장한다.
    // 글자처럼 취급 표는 이웃 문단을 절반 넘게 지나야 옮겨 가므로, 엔진이 돌려준 남은 거리(rest)를 다음 움직임에 더한다
    if (this.moveDragState.claudeStart == null) this.moveDragState.claudeStart = this.wasm.saveSnapshot();
    const carry = this.moveDragState.claudeCarry ?? 0;
    const result = this.wasm.moveTableOffset(ref.sec, ref.ppi, ref.ci, deltaH, deltaV + carry);
    this.moveDragState.claudeCarry = (result as any).rest ?? 0;
// ==== next ====
    if (totalDeltaH !== 0 || totalDeltaV !== 0) {
      this.executeOperation({ kind: 'record', command:
        new MoveTableCommand(
          tableRef.sec, startPpi, tableRef.ci,
          totalDeltaH, totalDeltaV,
          tableRef.ppi, tableRef.ci,
        ),
      });
    }
// ==== replace ====
    // [claude-hwpx table-move-undo] 표 이동은 문단 순서를 바꾸는 일이라 같은 거리를 반대로 끌어도 제자리로 오지 않는다
    // (되돌리면 표가 문서 끝으로 갔다, 2026-09-27 사용자 발견). 끌기 뒤 상태를 저장하고 시작 상태로 돌린 다음,
    // 「끌기 뒤 상태로 바꾸기」를 스냅숏 작업 한 번으로 기록한다. 되돌리기는 시작 상태를 그대로 복원한다
    const claudeStart = (state as any).claudeStart as number | undefined;
    if (claudeStart != null) {
      const after = this.wasm.saveSnapshot();
      this.wasm.restoreSnapshot(claudeStart);
      this.wasm.discardSnapshot(claudeStart);
      this.executeOperation({
        kind: 'snapshot',
        operationType: 'moveTable',
        operation: (w: any) => {
          w.restoreSnapshot(after);
          w.discardSnapshot(after);
          return { sectionIndex: tableRef.sec, paragraphIndex: tableRef.ppi, charOffset: 0 };
        },
      });
      this.cursor.updateSelectedTableRef(tableRef.sec, tableRef.ppi, tableRef.ci);
    } else if (totalDeltaH !== 0 || totalDeltaV !== 0) {
      this.executeOperation({ kind: 'record', command:
        new MoveTableCommand(
          tableRef.sec, startPpi, tableRef.ci,
          totalDeltaH, totalDeltaV,
          tableRef.ppi, tableRef.ci,
        ),
      });
    }
// ==== next ====
  const deltaYpx = py - this.moveDragState.lastPageY;
// ==== replace ====
  // [claude-hwpx table-move-undo] 쪽 기준 y 는 쪽 경계를 넘으면 쪽 높이만큼 튄다(위로 끌었는데 표가 아래로 멀리 갔다).
  // 세로 거리는 스크롤 영역 기준 y 로 잰다. 첫 움직임만 쪽 기준 차이를 쓴다(누른 곳의 스크롤 y 를 모른다)
  const claudeCy = cy / zoom;
  const deltaYpx = this.moveDragState.claudeLastCy == null
    ? py - this.moveDragState.lastPageY
    : claudeCy - this.moveDragState.claudeLastCy;
// ==== next ====
    this.moveDragState.lastPageY = py;
// ==== replace ====
    this.moveDragState.lastPageY = py;
    this.moveDragState.claudeLastCy = claudeCy;
