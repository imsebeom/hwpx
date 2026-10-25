// ==== find ====
                        let gap = next_seg.vertical_pos - (seg.vertical_pos + seg.line_height);
                        y_offset += hwpunit_to_px(gap, self.dpi);
// ==== replace ====
                        let gap = next_seg.vertical_pos - (seg.vertical_pos + seg.line_height);
                        y_offset += hwpunit_to_px(gap, self.dpi);
                        // [claude-hwpx tac-multi-om] 엔진이 만든 줄의 높이는 표와 바깥 여백 위아래를 담는다 — 다음 줄은
                        // 표 바닥 + 바깥 아래 여백 + 줄 간격에서 시작한다(한국문화 1단원 1쪽 한/글 PDF)
                        if self.profile.get().hwpx_container()
                            && crate::renderer::para_has_no_stored_line_segs(para)
                        {
                            if let Some(Control::Table(cur)) = para.controls.get(control_index) {
                                y_offset += hwpunit_to_px(cur.outer_margin_bottom as i32, self.dpi);
                            }
                        }
// ==== next ====
                        if Self::tac_stored_band_is_outer_box(para, t) {
// ==== replace ====
                        // [claude-hwpx tac-multi-om] 엔진이 만든 줄도 표 위에 바깥 위 여백을 둔다
                        if Self::tac_stored_band_is_outer_box(para, t)
                            || (self.profile.get().hwpx_container()
                                && crate::renderer::para_has_no_stored_line_segs(para))
                        {
