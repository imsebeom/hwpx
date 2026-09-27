// ==== find ====
        if let Some(json) = self.cursor_rect_in_cell_fast(
            section_idx,
            parent_para_idx,
            control_idx,
            cell_idx,
            cell_para_idx,
            char_offset,
        )? {
            return Ok(json);
        }
// ==== replace ====
        // [claude-hwpx cell-inline-caret-call] 글자처럼 취급 그림 옆 캐럿과 논리 위치 → 글자 위치
        let char_offset = match self.claude_cell_inline_caret(
            section_idx,
            parent_para_idx,
            control_idx,
            cell_idx,
            cell_para_idx,
            char_offset,
        )? {
            (Some(json), _) => return Ok(json),
            (None, off) => off,
        };
        if let Some(json) = self.cursor_rect_in_cell_fast(
            section_idx,
            parent_para_idx,
            control_idx,
            cell_idx,
            cell_para_idx,
            char_offset,
        )? {
            return Ok(json);
        }
