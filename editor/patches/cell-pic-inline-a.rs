// ==== find ====
        if !cell_path.is_empty() {
            if cell_path_is_textbox {
// ==== replace ====
        // [claude-hwpx cell-pic-inline] 표 칸 문단 안에 글자처럼 취급 그림으로 넣기. 엔진은 칸 그림을 칸 위에 뜬
        // 그림(표 옆 개체)으로만 넣었다. 호출자가 paperOffsetXHu 에 i32::MIN 을 주면 글상자 갈래와 같은 방식으로
        // 칸 문단에 끼우고 글자처럼 취급으로 만든다(에디터 cli image 가 쓴다, 2026-09-27)
        let claude_inline =
            !cell_path.is_empty() && !cell_path_is_textbox && paper_offset_x_hu == Some(i32::MIN);
        if !cell_path.is_empty() {
            if cell_path_is_textbox || claude_inline {
