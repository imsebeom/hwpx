// ==== find ====
            st.advance_column_or_new_page();
            // [claude-hwpx restrict-float-defer] 새 쪽 맨 위에 미룬 표부터
            if st.profile.hwpx_container()
                && !st.deferred_table_controls.is_empty()
                && st.current_items.is_empty()
            {
                self.flush_deferred_table_controls(st, paragraphs, claude_composed, styles, claude_measured, None);
            }
// ==== replace ====
            st.advance_column_or_new_page();
            // [claude-hwpx restrict-float-defer] 새 쪽 맨 위에 미룬 표부터
            if st.profile.hwpx_container()
                && !st.deferred_table_controls.is_empty()
                && st.current_items.is_empty()
            {
                self.flush_deferred_table_controls(st, paragraphs, claude_composed, styles, claude_measured, None);
            }
            // [claude-hwpx push-para-base] 통째로 넘어온 문단이 새 쪽 첫 항목이면 그 저장 줄 위치가 쪽 기준점이다(쪽 첫 항목 스냅과 같은 규칙).
            // 비워 두면 다음 문단이 이 문단 높이로 기준점을 거꾸로 셈해 줄 간격과 아래 간격을 한 번 더 센다(결과보고서 173번)
            if st.profile.hwpx_container() && st.col_count == 1 && st.current_items.is_empty() {
                if let Some(s0) = para.line_segs.first().filter(|s| !is_synthetic_line_seg(s)) {
                    st.vpos_col_anchor = st.current_height;
                    st.vpos_page_base = Some(s0.vertical_pos);
                    st.vpos_lazy_base = None;
                    st.vpos_page_base_stored = true;
                    st.vpos_ladder_dirty = false;
                }
            }
