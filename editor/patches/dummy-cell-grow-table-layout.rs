// ==== find ====
        if table.common.treat_as_char && self.profile.get().hwpx_container() {
            return;
        }
        let target_height = if table.common.height > 0 {
// ==== replace ====
        // [claude-hwpx dummy-cell-grow] 칸 문단 줄 위치가 모두 0 인 더미 줄 배치(생성기) 칸이 있으면 선언대로 키운다(서식2 c52 1×1 표: 한/글이 크게 그림)
        let claude_dummy_cells = table.cells.iter().any(|c| {
            c.paragraphs.len() >= 2
                && c.paragraphs.iter().all(|p| p.line_segs.first().is_some_and(|s| s.vertical_pos == 0))
        });
        if table.common.treat_as_char && self.profile.get().hwpx_container() && !claude_dummy_cells {
            return;
        }
        let target_height = if table.common.height > 0 {
