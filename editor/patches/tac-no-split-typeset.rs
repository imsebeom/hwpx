// ==== find ====
        if table.common.treat_as_char && table.row_count <= 1 && table_total <= available {
// ==== replace ====
        // [claude-hwpx tac-no-split] HWPX 는 여러 행 표도, 쪽보다 큰 표도 나누지 않는다. 남은 자리에 안 들면 다음 쪽 맨 위에 통째로,
        // 쪽 맨 위에서도 안 들면 그대로 두고 아래로 넘친다(결과보고서 사본 157, 163, 166번 표, 정답본 11건)
        let claude_tac_no_split = st.profile.hwpx_container() && table.common.treat_as_char;
        if claude_tac_no_split
            || (table.common.treat_as_char && table.row_count <= 1 && table_total <= available)
        {
// ==== next ====
            || (table.common.treat_as_char && table.row_count <= 1 && table_total <= available)
        {
            if !st.current_items.is_empty() {
                st.advance_column_or_new_page();
            }
// ==== replace ====
            || (table.common.treat_as_char && table.row_count <= 1 && table_total <= available)
        {
            // [claude-hwpx tac-no-split] 한 줄짜리 표 문단의 줄 뒤 간격은 쪽 끝을 넘어도 된다(tac-multi-fit-tail 과 같은 한/글 규칙). 결과보고서 21:11 판
            // 157번 표: 제목 뒤 1670 + 표 65456 = 67126 ≤ 본문 67182 라 한/글은 같은 쪽에 두는데, 간격 720 까지 세면 넘쳤다
            // 높이는 한/글이 저장한 표 줄(엔진이 만든 줄이 아닐 때)을 먼저 쓴다 — 엔진 행 측정이 한/글보다 클 때가 있다(157번: 879.4px 대 줄 872.7px)
            let claude_tac_h = match para.line_segs.as_slice() {
                [seg] if !is_synthetic_line_seg(seg) && seg.line_height > 0 => hwpunit_to_px(seg.line_height, self.dpi),
                _ => ft.effective_height,
            };
            let claude_fits_without_tail = claude_tac_no_split
                && st.current_height + ft.host_spacing.before + claude_tac_h <= available + 0.5;
            if !st.current_items.is_empty() && !claude_fits_without_tail {
                st.advance_column_or_new_page();
            }
// ==== next ====
            && st.current_height + declared_object_total <= available
            && !hwpx_tac_cell_leftover_missing_owned_line;
// ==== replace ====
            && st.current_height + declared_object_total <= available
            && !hwpx_tac_cell_leftover_missing_owned_line
            // [claude-hwpx tac-no-split] 한/글이 저장한 표 줄이 선언 높이보다 크면 선언이 낡은 것이다(157번 표: 선언 62047, 줄 66690 —
            // 한/글은 줄 높이로 재 다음 쪽으로 넘긴다). 그때는 선언 높이로 남은 자리에 넣지 않는다
            && !(st.profile.hwpx_container()
                && para.line_segs.len() == 1
                && para.line_segs.first().is_some_and(|seg| {
                    !is_synthetic_line_seg(seg)
                        && seg.line_height
                            > table.common.height.min(i32::MAX as u32) as i32
                                + i32::from(table.outer_margin_top)
                                + i32::from(table.outer_margin_bottom)
                                + 75
                }));
