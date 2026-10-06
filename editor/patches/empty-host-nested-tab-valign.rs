// ==== find ====
                            // 케이스는 nested_bottom 이 max 로 보정한다(#44 under-count 가드 보존).
                            Control::Table(_) => {}
// ==== replace ====
                            // 케이스는 nested_bottom 이 max 로 보정한다(#44 under-count 가드 보존).
                            // [claude-hwpx empty-host-nested-tab-valign] 단, 줄 배치가 합성된 빈 문단 하나에 든 위아래 배치 표는
                            // 저장 흐름도 문단 위치도 없어 위 두 보정이 그 표를 못 담는다(문단 위치가 모두 0). 측정 쪽
                            // empty-host-nested-tab 과 같이 빈 줄 대신 표 높이를 센다 — 빠지면 세로 가운데 정렬 칸이 표 높이의 절반만큼
                            // 내용을 내려 그렸다(한국문화 12단원 그림 칸 27.3px)
                            Control::Table(t)
                                if !t.common.treat_as_char
                                    && matches!(t.common.text_wrap, TextWrap::TopAndBottom)
                                    && para.controls.len() == 1
                                    && crate::renderer::para_has_no_stored_line_segs(para)
                                    && !para.text.chars().any(|ch| {
                                        ch > '\u{001F}' && ch != '\u{FFFC}' && !ch.is_whitespace()
                                    }) =>
                            {
                                // calc_nested_table_height 는 바깥 여백까지 담는다
                                let table_h = self.calc_nested_table_height(t, styles).max(
                                    hwpunit_to_px(t.common.height as i32, self.dpi)
                                        + hwpunit_to_px(t.outer_margin_top as i32, self.dpi)
                                        + hwpunit_to_px(t.outer_margin_bottom as i32, self.dpi),
                                );
                                let host_line = para
                                    .line_segs
                                    .first()
                                    .map(|s| hwpunit_to_px(s.line_height + s.line_spacing.max(0), self.dpi))
                                    .unwrap_or(0.0);
                                text_height += (table_h - host_line).max(0.0);
                            }
                            Control::Table(_) => {}
