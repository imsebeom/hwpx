// ==== find ====
        if is_wrap_around_table && pre_height > 0.0 {
            let v_off_px = crate::renderer::hwpunit_to_px(vertical_offset as i32, self.dpi);
            let table_bottom = v_off_px + table_total_height;
// ==== replace ====
        if is_wrap_around_table && pre_height > 0.0 {
            let v_off_px = crate::renderer::hwpunit_to_px(vertical_offset as i32, self.dpi);
            // [claude-hwpx para-float-text-host] 한/글은 표 바닥을 오프셋 + 바깥 여백 위 + 선언 높이 + 바깥 여백 아래로 잡는다(d160 p3: 1901+283+9258+283).
            // 표 전체 높이(table_total_height)는 바깥 여백 대신 문단 줄 간격을 품고 있어 그만큼 내려갔다
            let table_bottom = if st.profile.hwpx_stored_layout()
                && crate::renderer::para_has_no_stored_line_segs(para)
                && table.common.height > 0
            {
                v_off_px
                    + hwpunit_to_px(
                        i32::from(table.outer_margin_top)
                            + table.common.height as i32
                            + i32::from(table.outer_margin_bottom),
                        self.dpi,
                    )
            } else {
                v_off_px + table_total_height
            };
