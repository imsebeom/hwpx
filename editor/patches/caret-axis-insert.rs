// ==== find ====
        let effective_char_offset = char_offset.min(text_len);
        let control_positions = self.control_text_positions();
        let inserts_before_inline_control = char_offset <= text_len
// ==== replace ====
        let effective_char_offset = char_offset.min(text_len);
        let control_positions = self.control_text_positions();
        // [claude-hwpx caret-axis] 캐럿이 글자처럼 취급 개체 바로 뒤면 같은 글자 위치의 개체 뒤에 넣는다.
        // 표지가 없으면 종전처럼 개체 앞에 넣는다(캐럿 축에서 그 자리를 가리킬 수 없던 결함).
        let after_inline = INSERT_AFTER_INLINE_CONTROLS.with(|flag| flag.get());
        if after_inline && char_offset <= text_len && effective_char_offset == text_len && !self.char_offsets.is_empty() {
            let trailing = control_positions.iter().filter(|&&pos| pos >= text_len).count();
            if trailing > 0 {
                return self.insert_text_at(text_len + trailing, new_text);
            }
        }
        let inserts_before_inline_control = !after_inline
            && char_offset <= text_len
