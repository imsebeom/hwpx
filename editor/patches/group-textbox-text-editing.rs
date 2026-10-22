// ==== find ====
                if cell_idx != 0 {
                    return Err(HwpError::RenderError(format!(
                        "글상자 셀 인덱스는 0이어야 합니다 (요청: {})",
                        cell_idx
                    )));
                }
                let tb =
                    super::super::helpers::get_textbox_from_shape_mut(shape).ok_or_else(|| {
// ==== replace ====
                // [claude-hwpx group-textbox] 묶음이면 cell_idx 번째 자식의 글상자(다른 도형은 cell_idx 0 만)
                let tb =
                    super::super::helpers::claude_textbox_at_mut(shape, cell_idx).ok_or_else(|| {
// ==== next ====
                if let Some(tb) = super::super::helpers::get_textbox_from_shape_mut(shape) {
                    if let Some(cell_para) = tb.paragraphs.get_mut(cell_para_idx) {
// ==== replace ====
                if let Some(tb) = super::super::helpers::claude_textbox_at_mut(shape, cell_idx) {
                    if let Some(cell_para) = tb.paragraphs.get_mut(cell_para_idx) {
// ==== next ====
                let Some(textbox) = super::super::helpers::get_textbox_from_shape_mut(shape) else {
// ==== replace ====
                let Some(textbox) = super::super::helpers::claude_textbox_at_mut(shape, cell_idx) else {
// ==== next ====
                let tb = super::super::helpers::get_textbox_from_shape(shape)?;
                let common = shape.common();
                Some((common.width as i32, tb.margin_left, tb.margin_right))
// ==== replace ====
                let tb = super::super::helpers::claude_textbox_at(shape, cell_idx)?;
                let width = super::super::helpers::claude_textbox_owner_width(shape, cell_idx);
                Some((width, tb.margin_left, tb.margin_right))
// ==== next ====
                Control::Shape(s) => super::super::helpers::get_textbox_from_shape(s)?
                    .paragraphs
                    .get(cell_para_idx)?,
// ==== replace ====
                Control::Shape(s) => super::super::helpers::claude_textbox_at(s, cell_idx)?
                    .paragraphs
                    .get(cell_para_idx)?,
// ==== next ====
                if cell_idx != 0 {
                    return None;
                }
                get_textbox_from_shape(shape)?.paragraphs.get(cell_para_idx)
// ==== replace ====
                super::super::helpers::claude_textbox_at(shape, cell_idx)?.paragraphs.get(cell_para_idx)
// ==== next ====
                if let Some(tb) = super::super::helpers::get_textbox_from_shape_mut(shape) {
                    tb.paragraphs.insert(new_cell_para_idx, new_para);
// ==== replace ====
                if let Some(tb) = super::super::helpers::claude_textbox_at_mut(shape, cell_idx) {
                    tb.paragraphs.insert(new_cell_para_idx, new_para);
// ==== next ====
                if let Some(tb) = super::super::helpers::get_textbox_from_shape_mut(shape) {
                    let removed = tb.paragraphs.remove(cell_para_idx);
// ==== replace ====
                if let Some(tb) = super::super::helpers::claude_textbox_at_mut(shape, cell_idx) {
                    let removed = tb.paragraphs.remove(cell_para_idx);
// ==== next ====
                let text_box = get_textbox_from_shape(shape)
                    .ok_or_else(|| HwpError::RenderError("도형에 글상자가 없습니다".to_string()))?;
                Ok(text_box.paragraphs.len())
// ==== replace ====
                let text_box = super::super::helpers::claude_textbox_at(shape, cell_idx)
                    .ok_or_else(|| HwpError::RenderError("도형에 글상자가 없습니다".to_string()))?;
                Ok(text_box.paragraphs.len())
// ==== next ====
                    if cell_idx != 0 {
                        return Err(HwpError::RenderError(format!(
                            "경로[{}]: 글상자의 cell_index는 0이어야 합니다 ({})",
                            i, cell_idx
                        )));
                    }
                    let text_box = super::super::helpers::get_textbox_from_shape_mut(shape)
// ==== replace ====
                    let text_box = super::super::helpers::claude_textbox_at_mut(shape, cell_idx)
