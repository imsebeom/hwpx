// ==== find ====
            self.document.sections[section_idx].paragraphs[para_idx]
                .insert_text_at(char_offset, &clip_text);

            // 클립보드의 글자 모양 적용
            self.apply_clipboard_char_shapes(
                section_idx,
                para_idx,
                char_offset,
// ==== replace ====
            // [claude-hwpx caret-axis paste-body] char_offset 은 캐럿 축 — 개체 뒤면 개체 뒤에 넣는다
            let text_offset = crate::document_core::helpers::insert_text_at_caret(
                &mut self.document.sections[section_idx].paragraphs[para_idx],
                char_offset,
                &clip_text,
            );

            // 클립보드의 글자 모양 적용
            self.apply_clipboard_char_shapes(
                section_idx,
                para_idx,
                text_offset,
