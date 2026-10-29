// ==== find ====
                let combined: f64 = (r..r + span).map(|i| row_heights[i]).sum();
// ==== replace ====
                // [claude-hwpx span-ladder-trust] HWPX 글자처럼 취급 표의 걸친 칸: 뒤 줄이 그림 아래에서 시작하면 저장 줄이 그림 자리를 담았다 — 그림을 또 더하지 않는다
                // (결과보고서 160번 표 10행: 한/글 58.3px = 줄 끝 4084 + 여백, 엔진 65.7px)
                let required_height = if !self.is_native_hwp5
                    && !self.is_hwp3_variant
                    && table.common.treat_as_char
                    && non_inline_h > 0.0
                    && cell.text_direction == 0
                    && cell.paragraphs.iter().all(|p| {
                        !p.line_segs.is_empty() && p.line_segs.iter().all(|s| s.tag & 0x8000_0000 == 0)
                    })
                    && cell.paragraphs.iter().enumerate().any(|(i, pp)| {
                        let obj_h = pp
                            .controls
                            .iter()
                            .filter_map(|c| match c {
                                Control::Picture(pic) if !pic.common.treat_as_char => {
                                    Some(self.non_inline_control_flow_height(&pic.common))
                                }
                                Control::Shape(sh) if !sh.common().treat_as_char => {
                                    Some(self.non_inline_control_flow_height(sh.common()))
                                }
                                _ => None,
                            })
                            .fold(0.0f64, f64::max);
                        let own_top = pp
                            .line_segs
                            .first()
                            .map(|s| hwpunit_to_px(s.vertical_pos, self.dpi))
                            .unwrap_or(0.0);
                        obj_h > 0.0
                            && cell.paragraphs[i + 1..]
                                .iter()
                                .find_map(|later| later.line_segs.first())
                                .is_some_and(|s| hwpunit_to_px(s.vertical_pos, self.dpi) + 0.5 >= own_top + obj_h)
                    }) {
                    let (mut next_top, mut end) = (0i64, 0i64);
                    for s in cell.paragraphs.iter().flat_map(|p| p.line_segs.iter()) {
                        let top = i64::from(s.vertical_pos).max(next_top);
                        end = end.max(top + i64::from(s.line_height));
                        next_top = top + i64::from(s.line_height) + i64::from(s.line_spacing.max(0));
                    }
                    hwpunit_to_px(end as i32, self.dpi).max(nested_bottom).max(wrap_bottom) + pad_top + pad_bottom
                } else {
                    required_height
                };
                let combined: f64 = (r..r + span).map(|i| row_heights[i]).sum();
