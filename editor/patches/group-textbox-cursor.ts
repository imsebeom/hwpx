// ==== find ====
        ctrlTextPos: 0, // Rust가 재계산
        cellIdx: 0,
        isTextBox: true,
// ==== replace ====
        ctrlTextPos: 0, // Rust가 재계산
        // [claude-hwpx group-textbox-cursor] 묶음 안 글상자는 칸 번호에 묶음 자식 경로가 실려 있다(엔진 group-textbox).
        // 0 으로 두면 글을 친 뒤 커서가 다른 자식을 가리켜 제자리에 멈췄다(사용자 보고 2026-10-23 워크시트 hwp)
        cellIdx: pos.cellIndex ?? 0,
        isTextBox: true,
// ==== next ====
          controlIndex: last.ctrlIdx,
          cellIndex: 0,
          cellParaIndex: result.para,
          isTextBox: true,
// ==== replace ====
          controlIndex: last.ctrlIdx,
          cellIndex: last.cellIdx ?? 0, // [claude-hwpx group-textbox-cursor] 묶음 자식 경로를 지킨다
          cellParaIndex: result.para,
          isTextBox: true,
