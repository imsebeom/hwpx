// ==== find ====
                    if cell_idx != 0 {
                        return Err(HwpError::RenderError(format!(
                            "경로[{}]: 글상자의 cell_index는 0이어야 합니다 ({})",
                            i, cell_idx
                        )));
                    }
                    let text_box = get_textbox_from_shape_mut(shape).ok_or_else(|| {
// ==== replace ====
                    // [claude-hwpx group-textbox] 묶음이면 칸 번호에 실은 자식 경로의 글상자
                    let text_box = crate::document_core::helpers::claude_textbox_at_mut(shape, cell_idx).ok_or_else(|| {
// ==== next ====
                    if cell_idx != 0 {
                        return Err(HwpError::RenderError(format!(
                            "경로[{}]: 글상자의 cell_index는 0이어야 합니다 ({})",
                            i, cell_idx
                        )));
                    }
                    let text_box = get_textbox_from_shape(shape.as_ref()).ok_or_else(|| {
// ==== replace ====
                    // [claude-hwpx group-textbox] 묶음이면 칸 번호에 실은 자식 경로의 글상자
                    let text_box = crate::document_core::helpers::claude_textbox_at(shape.as_ref(), cell_idx).ok_or_else(|| {
