// ==== find ====
  // 개체 설명문 생성 (한컴 기본 패턴)
// ==== replace ====
  // [claude-hwpx cell-pic-place] 표 칸(표 속 표 칸 포함)을 누르면 그 칸 문단의 누른 자리에 글자처럼 취급으로 넣는다(한글처럼 칸 안에).
  // 종전에는 표를 담은 본문 문단에 붙은 떠 있는 그림(어울림)으로 들어가 표 위에 얹히고 칸을 따라 움직이지 않았다.
  // 엔진 cell-pic-inline 의 약속값(paperOffsetXHu = i32::MIN)을 쓰고, 칸 안쪽 폭을 넘으면 비례로 줄인다
  if (inCell) {
    paperOffsetXHu = -2147483648;
    paperOffsetYHu = 0;
    try {
      const path = hit.cellPath;
      const last = path[path.length - 1];
      const cp = path.length > 1
        ? this.wasm.getCellPropertiesByPath(sec, paraIdx, JSON.stringify(path), last.cellIndex)
        : this.wasm.getCellProperties(sec, paraIdx, last.controlIndex, last.cellIndex);
      const inner = cp.width - cp.paddingLeft - cp.paddingRight;
      if (inner > 0 && wHwp > inner) {
        hHwp = Math.round(hHwp * inner / wHwp);
        wHwp = inner;
      }
    } catch { /* 칸 속성 조회 실패면 본문 폭 기준 크기 그대로 */ }
  }

  // 개체 설명문 생성 (한컴 기본 패턴)
