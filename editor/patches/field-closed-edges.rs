// ==== find ====
        let inserted_len = new_chars.len();
        for fr in &mut self.field_ranges {
            if fr.start_char_idx > char_offset {
                fr.start_char_idx += inserted_len;
            }
            if fr.end_char_idx >= char_offset {
                fr.end_char_idx += inserted_len;
            }
        }
// ==== replace ====
        let inserted_len = new_chars.len();
        // [claude-hwpx field-closed-edges] 하이퍼링크, 상호 참조, 날짜, 문서 요약 필드는 경계에 친 글을 품지 않는다
        // (한/글과 같게). 누름틀은 끝에 친 글이 값이 되어야 하므로 종전대로 늘어난다.
        let closed: Vec<usize> = self
            .controls
            .iter()
            .enumerate()
            .filter_map(|(i, c)| match c {
                crate::model::control::Control::Field(f)
                    if matches!(
                        f.field_type,
                        crate::model::control::FieldType::Hyperlink
                            | crate::model::control::FieldType::CrossRef
                            | crate::model::control::FieldType::Date
                            | crate::model::control::FieldType::DocDate
                            | crate::model::control::FieldType::Summary
                    ) =>
                {
                    Some(i)
                }
                _ => None,
            })
            .collect();
        for fr in &mut self.field_ranges {
            if closed.contains(&fr.control_idx) {
                if fr.start_char_idx >= char_offset {
                    fr.start_char_idx += inserted_len;
                    fr.end_char_idx += inserted_len;
                } else if fr.end_char_idx > char_offset {
                    fr.end_char_idx += inserted_len;
                }
                continue;
            }
            if fr.start_char_idx > char_offset {
                fr.start_char_idx += inserted_len;
            }
            if fr.end_char_idx >= char_offset {
                fr.end_char_idx += inserted_len;
            }
        }
