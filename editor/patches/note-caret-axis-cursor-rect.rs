// ==== find ====
        let footnote_marker_positions: Vec<(usize, usize)> = self
            .get_render_paragraph_ref(section_idx, para_idx)
            .ok()
            .map(|para| {
                let ctrl_positions = find_logical_control_positions(para);
                para.controls
                    .iter()
                    .enumerate()
                    .filter(|(_, ctrl)| matches!(ctrl, Control::Footnote(_) | Control::Endnote(_)))
                    .filter_map(|(ci, _)| ctrl_positions.get(ci).copied().map(|pos| (ci, pos)))
                    .collect()
            })
            .unwrap_or_default();
// ==== replace ====
        // [claude-hwpx note-caret-axis] 표지 자리는 각주를 세지 않는 캐럿 축(글 넣기와 같은 축)
        let footnote_marker_positions: Vec<(usize, usize)> = self
            .get_render_paragraph_ref(section_idx, para_idx)
            .ok()
            .map(crate::document_core::helpers::claude_note_caret_positions)
            .unwrap_or_default();
// ==== next ====
                        if offset == *marker_pos || offset == *marker_pos + 1 {
                            return Some(CursorHit {
                                page_index,
                                x: if offset == *marker_pos {
                                    node.bbox.x
                                } else {
                                    node.bbox.x + node.bbox.width
                                },
// ==== replace ====
                        // [claude-hwpx note-caret-axis] 표지 자리 캐럿은 표지 앞(그 자리에 넣은 글은 각주 앞에 들어간다). 다음 자리는 글자 조각이 그린다
                        if offset == *marker_pos {
                            return Some(CursorHit {
                                page_index,
                                x: node.bbox.x,
