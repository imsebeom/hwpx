// ==== find ====
            .filter(|&&p| p >= self_text_len)
            .count() as u32
            * 8;
        let utf16_end: u32 = if !self.char_offsets.is_empty() {
// ==== replace ====
            .filter(|&&p| p >= self_text_len)
            .count() as u32
            * 8
            // [claude-hwpx merge-field-end] 글 끝에서 닫히는 필드의 끝 표식도 8칸이다(컨트롤이 아니라 위에서 안 잡힌다)
            + self
                .field_ranges
                .iter()
                .filter(|f| f.end_char_idx >= self_text_len)
                .count() as u32
                * 8;
        let utf16_end: u32 = if !self.char_offsets.is_empty() {
// ==== next ====
        self.char_count = self.text.chars().map(Self::char_stream_len).sum::<u32>()
            + self.controls.len() as u32 * 8
            + 1;

        // 7. has_para_text: 병합 후 텍스트/컨트롤이 있으면 PARA_TEXT 필요
// ==== replace ====
        self.char_count = self.text.chars().map(Self::char_stream_len).sum::<u32>()
            + self.controls.len() as u32 * 8
            // [claude-hwpx merge-field-end] 끝 표식
            + (self.field_ranges.len() + self.orphan_field_ends.len()) as u32 * 8
            + 1;

        // 7. has_para_text: 병합 후 텍스트/컨트롤이 있으면 PARA_TEXT 필요
// ==== next ====
        let ctrl_code_units: u32 = self.controls.len() as u32 * 8;
        self.char_count = kept_text_code_units + ctrl_code_units + 1; // +1 for paragraph end marker
// ==== replace ====
        // [claude-hwpx merge-field-end] 남은 필드의 끝 표식도 8칸이다
        let ctrl_code_units: u32 =
            (self.controls.len() + self.field_ranges.len() + self.orphan_field_ends.len()) as u32 * 8;
        self.char_count = kept_text_code_units + ctrl_code_units + 1; // +1 for paragraph end marker
