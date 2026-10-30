// ==== find ====
            if tac_above_offset_float_flow.is_some() {
                y_offset = para_y_for_table;
            }
// ==== replace ====
            if tac_above_offset_float_flow.is_some() {
                y_offset = para_y_for_table;
                // [claude-hwpx offset-float-om] 저장 밴드가 바깥 위 여백 + 표 + 바깥 아래 여백이면 표는 줄 맨 위 + 위 여백(c18 6×6 표: 한/글 +283)
                if self.profile.get().hwpx_container() {
                    if let Some(Control::Table(t)) = para.controls.get(control_index) {
                        if Self::tac_stored_band_is_outer_box(para, t) {
                            y_offset += hwpunit_to_px(t.outer_margin_top as i32, self.dpi);
                        }
                    }
                }
            }
