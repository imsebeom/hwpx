// ==== find ====
            } else if let Some(extras_hu) = empty_host_physical_extras_hu {
                st.current_height +=
                    pre_height + table_total_height + hwpunit_to_px(extras_hu as i32, self.dpi);
// ==== replace ====
            } else if let Some(extras_hu) = empty_host_physical_extras_hu {
                // [claude-hwpx empty-host-block] 한/글 공식: 오프셋 + 바깥 여백 위아래(extras) + 선언 표 높이. host 형식 높이(table_total_height)는
                // 바깥 여백 등을 이미 품고 있어 extras 와 겹쳤다(d329). 선언 높이가 없으면 종전 값.
                let declared = hwpunit_to_px(table.common.height as i32, self.dpi);
                let body = if declared > 1.0 { declared } else { table_total_height };
                st.current_height += pre_height + body + hwpunit_to_px(extras_hu as i32, self.dpi);
