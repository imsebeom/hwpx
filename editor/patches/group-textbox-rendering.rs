// ==== find ====
                let valid = super::super::helpers::get_textbox_from_shape(shape)
                    .is_some_and(|textbox| cell_para_idx < textbox.paragraphs.len());
// ==== replace ====
                // [claude-hwpx group-textbox] 묶음 자식 글상자(칸 번호에 자식 경로)도 검증한다
                let valid = super::super::helpers::claude_textbox_at(shape, cell_idx)
                    .is_some_and(|textbox| cell_para_idx < textbox.paragraphs.len());
