// ==== find ====
    const natW = img.naturalWidth;
    const natH = img.naturalHeight;
// ==== replace ====
    // [claude-hwpx cell-pic-paste] 칸 안에 붙이면 너비를 칸 안쪽 폭에 맞추고 높이는 비율대로(한글 방식, 그림 넣기와 끌어 놓기와 같다).
    // 넣는 자리도 칸 문단 안 글자처럼 취급(엔진 cell-pic-inline 약속값). 종전에는 표를 담은 본문 문단의 떠 있는 그림으로 들어가
    // 크기가 본문 폭 기준이었다
    const pasteInCell = (pos.cellPath?.length ?? 0) > 0 && pos.parentParaIndex !== undefined && pos.isTextBox !== true;
    if (pasteInCell) {
      try {
        const path = pos.cellPath!;
        const last = path[path.length - 1];
        const cp = path.length > 1
          ? this.wasm.getCellPropertiesByPath(pos.sectionIndex, pos.parentParaIndex!, JSON.stringify(path), last.cellIndex)
          : this.wasm.getCellProperties(pos.sectionIndex, pos.parentParaIndex!, last.controlIndex, last.cellIndex);
        const inner = cp.width - cp.paddingLeft - cp.paddingRight;
        if (inner > 0 && wHwp > 0) {
          hHwp = Math.round(hHwp * inner / wHwp);
          wHwp = inner;
        }
      } catch { /* 칸 속성 조회 실패면 본문 폭 기준 크기 그대로 */ }
    }

    const natW = img.naturalWidth;
    const natH = img.naturalHeight;
// ==== next ====
      const result = wasm.insertPicture(
        p.sectionIndex, paraForCall, p.charOffset,
        cellPathJson, data, wHwp, hHwp, natW, natH, ext, '',
      );
      if (result.ok) {
// ==== replace ====
      const result = wasm.insertPicture(
        p.sectionIndex, paraForCall, p.charOffset,
        cellPathJson, data, wHwp, hHwp, natW, natH, ext, '',
        inCell && pasteInCell ? -2147483648 : undefined,
        inCell && pasteInCell ? 0 : undefined,
      );
      if (result.ok && inCell && pasteInCell) {
        const logical = typeof (result as any).logicalOffset === 'number' ? (result as any).logicalOffset : p.charOffset + 1;
        return { ...p, charOffset: logical } as DocumentPosition;
      }
      if (result.ok) {
