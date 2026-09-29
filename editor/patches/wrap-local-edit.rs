// ==== find ====
        let flow_before = body_paragraph_flow_signature(
            &self.document.sections[section_idx].paragraphs[para_idx],
        );
        let old_col = self
// ==== replace ====
        // [claude-hwpx wrap-local-edit] 스튜디오는 짧은 입력을 이 빠른 경로로 보내는데, 여기서는 문단만 다시 나눠
        // 그림 띠(글자처럼 취급하지 않는 그림 옆 줄)를 무시했다 — 그림 옆에서 치면 글이 그림 밑으로 겹쳤다.
        // 띠에 속한 문단이면 띠를 거치는 일반 삭제, 삽입으로 처리하고 흐름이 바뀌었다고 알려 쪽을 다시 그리게 한다
        if self
            .picture_band_owning_body_paragraph(section_idx, para_idx)
            .is_some()
        {
            if delete_count > 0 {
                self.delete_text_native(section_idx, para_idx, char_offset, delete_count)?;
            }
            if new_chars_count > 0 {
                self.insert_text_native(section_idx, para_idx, char_offset, text)?;
            }
            return Ok(super::super::helpers::json_ok_with(&format!(
                "\"charOffset\":{},\"documentPaginationPending\":false,\"flowChanged\":true",
                char_offset + new_chars_count
            )));
        }
        let flow_before = body_paragraph_flow_signature(
            &self.document.sections[section_idx].paragraphs[para_idx],
        );
        let old_col = self
