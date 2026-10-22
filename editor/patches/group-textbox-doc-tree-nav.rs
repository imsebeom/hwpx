// ==== find ====
            if let Control::Shape(s) = ctrl {
                let tb = get_textbox_from_shape(s.as_ref())?;
// ==== replace ====
            if let Control::Shape(s) = ctrl {
                // [claude-hwpx group-textbox] 묶음이면 칸 번호에 실은 자식 경로의 글상자
                let tb = crate::document_core::helpers::claude_textbox_at(s.as_ref(), entry.cell_idx)?;
