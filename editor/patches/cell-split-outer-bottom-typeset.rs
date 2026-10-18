// ==== find ====
            let mut budget = (avail_for_rows - consumed - cs_before - padding).max(0.0);
// ==== replace ====
            // [claude-hwpx cell-split-outer-bottom] HWPX CELL 표를 쪽 끝에서 행 안으로 자를 때 한/글은 바깥 여백 아래를 남긴다(d243 실험: 여백 변화량만큼 경계 이동)
            let claude_outer_bottom = if st.profile.hwpx_container()
                && !table.common.treat_as_char
                && matches!(
                    table.page_break,
                    crate::model::table::TablePageBreak::RowBreak
                ) {
                hwpunit_to_px(table.outer_margin_bottom as i32, self.dpi)
            } else {
                0.0
            };
            let mut budget =
                (avail_for_rows - consumed - cs_before - padding - claude_outer_bottom).max(0.0);
