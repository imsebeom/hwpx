// ==== find ====
        let tac_trailing_spacing_for_fit = if hwpx_rowbreak_tac_missing_owned_line {
            (fmt.total_height - fmt.height_for_fit).max(0.0)
        } else {
            0.0
        };
// ==== replace ====
        let tac_trailing_spacing_for_fit = if hwpx_rowbreak_tac_missing_owned_line {
            (fmt.total_height - fmt.height_for_fit).max(0.0)
        // [claude-hwpx tac-multi-fit-tail] 표가 여럿 든 글 없는 HWPX 문단은 표 줄의 뒤 간격이 쪽 끝을 넘어도 된다(d334 p89: 한/글이 첫 표를 쪽 끝에 둔다)
        } else if st.profile.hwpx_container()
            && prior_tac + 1 < tac_count
            && !para_has_visible_text(para)
            && tac_seg_idx < fmt.line_heights.len()
        {
            -(fmt.line_advance(tac_seg_idx) - fmt.line_heights[tac_seg_idx]).clamp(0.0, table_height)
        } else {
            0.0
        };
