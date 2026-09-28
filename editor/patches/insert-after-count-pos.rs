// ==== find ====
        let utf16_insert_pos: u32 = if char_offset > text_len && !self.char_offsets.is_empty() {
// ==== replace ====
        let utf16_insert_pos: u32 = if let Some(pos) = claude_after_pos {
            // [claude-hwpx insert-after-count-pos] 같은 글자 위치 개체 n 개 뒤(caret-axis-insert 에서 셈)
            pos
        } else if char_offset > text_len && !self.char_offsets.is_empty() {
