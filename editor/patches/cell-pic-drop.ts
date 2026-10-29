// ==== find ====
          ext,
          desc,
          undefined,
          undefined,
        );
// ==== replace ====
          ext,
          desc,
          // [claude-hwpx cell-pic-drop] 그림 파일을 칸(표 속 표 칸 포함)에 끌어 놓으면 칸 문단 안에 글자처럼 취급으로(엔진 cell-pic-inline 약속값)
          inCell ? -2147483648 : undefined,
          inCell ? 0 : undefined,
        );
// ==== next ====
    const { width, height } = fitDroppedImageSizeRaw(naturalWidth, naturalHeight, pageInfo, pagePoint.pageX);
// ==== replace ====
    let { width, height } = fitDroppedImageSizeRaw(naturalWidth, naturalHeight, pageInfo, pagePoint.pageX);
    // [claude-hwpx cell-pic-drop] 칸에 놓으면 너비를 칸 안쪽 폭에 맞추고 높이는 비율대로(한글 방식, 그림 넣기와 붙여넣기와 같다)
    if (inCell) {
      try {
        const last = cellPath[cellPath.length - 1];
        const cp = cellPath.length > 1
          ? (this.wasm as any).getCellPropertiesByPath(sec, paraIdx, JSON.stringify(cellPath), last.cellIndex)
          : this.wasm.getCellProperties(sec, paraIdx, last.controlIndex, last.cellIndex);
        const inner = cp.width - cp.paddingLeft - cp.paddingRight;
        if (inner > 0 && width > 0) {
          height = Math.round(height * inner / width);
          width = inner;
        }
      } catch { /* 칸 속성 조회 실패면 본문 기준 크기 그대로 */ }
    }
