// ==== find ====
        let mut fn_margin = if total_footnote > 0.0 {
            if next_starts_new_page
                || internal_reset_tail_uses_actual_footnote_boundary
// ==== replace ====
        // [claude-hwpx cellnote-split-end] 한/글은 쪽에 걸친 표의 칸 각주를 표가 끝나는 쪽에 둔다 — 이 쪽에 표 전체가 안 들어가면(조각으로 나뉘면)
        // 칸 각주를 미리 빼지 않는다(사본 실험 13/13, 가이드북 파트2 합본 117쪽)
        if st.profile.hwpx_container()
            && st.col_count == 1
            && !table.common.treat_as_char
            && ft.table_footnote_count > 0
            && st.current_height + table_total
                > st.base_available_height() - st.projected_footnote_height(0.0, 0) - st.current_zone_y_offset + 0.5
        {
            total_footnote = st.projected_footnote_height(0.0, 0);
        }
        let mut fn_margin = if total_footnote > 0.0 {
            if next_starts_new_page
                || internal_reset_tail_uses_actual_footnote_boundary
