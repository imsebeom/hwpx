// ==== find ====
                    if cell_idx != 0 {
                        return Err(HwpError::RenderError(format!(
                            "경로[{}]: 글상자의 cell_index는 0이어야 합니다 ({})",
                            i, cell_idx
                        )));
                    }
                    let text_box = get_textbox_from_shape(shape).ok_or_else(|| {
// ==== replace ====
                    // [claude-hwpx group-textbox] 경로 검사: 묶음이면 칸 번호에 실은 자식 경로의 글상자
                    let text_box = crate::document_core::helpers::claude_textbox_at(shape, cell_idx).ok_or_else(|| {
// ==== next ====
                    let text_box = get_textbox_from_shape(shape).ok_or_else(|| {
                        HwpError::RenderError(format!("경로[{}]: 글상자가 아닙니다", i))
// ==== replace ====
                    // [claude-hwpx group-textbox] 묶음이면 칸 번호에 실은 자식 경로의 글상자
                    let text_box = crate::document_core::helpers::claude_textbox_at(shape, cell_idx).ok_or_else(|| {
                        HwpError::RenderError(format!("경로[{}]: 글상자가 아닙니다", i))
// ==== next ====
                let text_box = get_textbox_from_shape(shape)
                    .ok_or_else(|| HwpError::RenderError("글상자가 아닙니다".to_string()))?;
// ==== replace ====
                // [claude-hwpx group-textbox] 묶음이면 칸 번호에 실은 자식 경로의 글상자
                let text_box = crate::document_core::helpers::claude_textbox_at(shape, last.1)
                    .ok_or_else(|| HwpError::RenderError("글상자가 아닙니다".to_string()))?;
// ==== next ====
            let is_tb = cei == 0
                && self
// ==== replace ====
            // [claude-hwpx group-textbox] 도형이면 칸 번호(묶음 자식 경로)와 상관없이 글상자
            let is_tb = self
