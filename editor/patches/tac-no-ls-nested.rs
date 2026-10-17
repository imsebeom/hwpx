// ==== find ====
                        if para_max_lh >= nested.common.height as i32 {
                            return None; // 줄높이가 이미 담고 있다
                        }
// ==== replace ====
                        if para_max_lh >= nested.common.height as i32 {
                            // [claude-hwpx tac-no-ls-nested] rhwp#7419 — 저장 줄이 아니라 선언높이로 합성한
                            // 줄(NO_LS)이면 줄높이는 선언만 담는다. 중첩 표가 내용으로 선언보다 자랐으면 그
                            // 차이만 더한다(재현: 안쪽 표 선언 64.0px, 측정 70.5px → 바깥 칸이 6.5px 모자라
                            // 안쪽 표 둘째 줄이 칸 밖으로 나갔다). 저장 줄은 종전대로 신뢰한다.
                            if !crate::renderer::para_has_no_stored_line_segs(p) {
                                return None; // 줄높이가 이미 담고 있다
                            }
                            let stretch = self.render_normalization.nested_table_width_scale(nested);
                            let mt = self.measure_table_impl(nested, 0, 0, styles, depth + 1, stretch);
                            // 합성 줄은 「적힌 높이 + 바깥 여백」이므로 표도 바깥 여백까지 센다(한/글 줄 = 표 + 바깥 여백.
                            // 2026-10-17 KTX 자료 1: 여백 141+141 을 빼고 재서 바깥 칸이 3.8px 모자랐다)
                            let om = hwpunit_to_px(nested.outer_margin_top as i32, self.dpi)
                                + hwpunit_to_px(nested.outer_margin_bottom as i32, self.dpi);
                            let grown = mt.total_height + om - hwpunit_to_px(para_max_lh, self.dpi);
                            return (grown > 0.5).then_some(grown);
                        }