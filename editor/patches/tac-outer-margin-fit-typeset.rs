// ==== find ====
        let hwpx_noninline_tac_measured_fit = self.profile.get().hwpx_stored_layout()
// ==== replace ====
        // [claude-hwpx tac-outer-margin-fit] 한/글은 이 표의 줄 높이를 선언 높이 + 바깥 여백 위아래로 잡고 쪽 끝 맞춤도 그 높이로 본다(d114 p31: 3263+139+139)
        let claude_tac_outer_margin_px = hwpunit_to_px(
            i32::from(table.outer_margin_top) + i32::from(table.outer_margin_bottom),
            self.dpi,
        );
        let hwpx_noninline_tac_measured_fit = self.profile.get().hwpx_stored_layout()
// ==== next ====
            && matches!(table.page_break, crate::model::table::TablePageBreak::None)
            && ft.table_footnotes.is_empty()
            && st.current_height + ft.effective_height <= available + 0.5;
        let declared_fit_height = if hwpx_noninline_tac_measured_fit {
            ft.effective_height
        } else {
// ==== replace ====
            && matches!(table.page_break, crate::model::table::TablePageBreak::None)
            && ft.table_footnotes.is_empty()
            && st.current_height + ft.effective_height + claude_tac_outer_margin_px <= available + 0.5;
        let declared_fit_height = if hwpx_noninline_tac_measured_fit {
            ft.effective_height + claude_tac_outer_margin_px
        } else {
