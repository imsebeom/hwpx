// ==== find ====
            && !saved_tac_table_bottom_fits
            && !st.current_items.is_empty())
            || stored_vpos_rewind_break
        {
            st.advance_column_or_new_page();
        }
// ==== replace ====
            && !saved_tac_table_bottom_fits
            && !st.current_items.is_empty())
            || stored_vpos_rewind_break
            // [claude-hwpx pagenum-tac-break] 앞에 쪽 번호 컨트롤이 있는 표는 첫 항목이 아니다. 자리가 모자라면 쪽 번호만 남기고 다음 쪽으로
            || (st.profile.hwpx_container()
                && st.current_height <= 0.5
                && st.current_items.is_empty()
                // 한/글이 저장한 줄이 표를 품고 있으면 그 쪽에 들어간 것이다(d100, d172). 더미나 합성 줄일 때만
                && (para.line_segs.get(1).is_some_and(|s| s.vertical_pos == 0)
                    || para.line_segs.first().is_some_and(|s| {
                        s.tag & crate::model::paragraph::LineSeg::TAG_IMPLEMENTATION_PROPERTY == 0 && s.line_height * 2 < table.common.height as i32
                    }))
                && table_height.max(crate::renderer::hwpunit_to_px(table.common.height as i32, self.dpi)) + para.line_segs.first().map_or(0.0, |s| crate::renderer::hwpunit_to_px(s.line_height, self.dpi)) > available
                && para.controls.iter().any(|c| matches!(c, Control::PageNumberPos(_))))
        {
            st.advance_column_or_new_page();
        }
