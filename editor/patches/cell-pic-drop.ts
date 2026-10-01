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
