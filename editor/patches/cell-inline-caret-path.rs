// ==== find ====
        let _para = self.resolve_paragraph_by_path(section_idx, parent_para_idx, &path)?;
// ==== replace ====
        let _para = self.resolve_paragraph_by_path(section_idx, parent_para_idx, &path)?;
        // [claude-hwpx cell-inline-caret-path] 한 겹 칸이면 글자처럼 취급 그림 옆 캐럿을 먼저 본다
        let char_offset = if path.len() == 1 {
            let (c0, c1, c2) = path[0];
            match self.claude_cell_inline_caret(section_idx, parent_para_idx, c0, c1, c2, char_offset)? {
                (Some(json), _) => return Ok(json),
                (None, off) => off,
            }
        } else {
            char_offset
        };
