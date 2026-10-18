// ==== find ====
        Ok(format!(
            "{{\"ok\":true,\"sectionIdx\":{},\"paraIdx\":{},\"controlIdx\":{},\"sourceType\":\"{}\"}}",
            section_idx, para_idx, control_idx, source_type
        ))
// ==== replace ====
        // [claude-hwpx fn-cell-target] 표 칸 출처면 칸 위치를 함께 준다(에디터가 칸 안 각주를 등록해 편집에 들어간다)
        let claude_cell = match &fn_ref.source {
            FootnoteSource::TableCell {
                cell_index,
                cell_para_index,
                cell_control_index,
                ..
            } => format!(
                ",\"cellIdx\":{},\"cellParaIdx\":{},\"cellControlIdx\":{}",
                cell_index, cell_para_index, cell_control_index
            ),
            _ => String::new(),
        };
        Ok(format!(
            "{{\"ok\":true,\"sectionIdx\":{},\"paraIdx\":{},\"controlIdx\":{},\"sourceType\":\"{}\"{}}}",
            section_idx, para_idx, control_idx, source_type, claude_cell
        ))
