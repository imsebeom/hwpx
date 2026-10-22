// ==== find ====
                Control::Shape(s) => {
                    &mut super::super::helpers::get_textbox_from_shape_mut(s)
                        .ok_or_else(|| HwpError::RenderError("글상자 없음".to_string()))?
// ==== replace ====
                Control::Shape(s) => {
                    // [claude-hwpx group-textbox] 묶음이면 칸 번호에 실은 자식 경로의 글상자
                    &mut super::super::helpers::claude_textbox_at_mut(s, cell_idx)
                        .ok_or_else(|| HwpError::RenderError("글상자 없음".to_string()))?
