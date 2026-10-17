// ==== find ====
                                text_height += (table_h - host_line).max(0.0);
                            }
                            Control::Table(_) => {}
// ==== replace ====
                                text_height += (table_h - host_line).max(0.0);
                            }
                            // [claude-hwpx cell-tac-nested-valign] 줄 배치가 합성된 문단의 글자처럼 취급 표는 합성 줄이 표의 적힌
                            // 높이만 담는다. 측정(height_measurer tac-no-ls-nested)은 표가 내용으로 자란 몫을 행 높이에 더하는데 여기서는
                            // 빠져, 세로 가운데 정렬 칸이 그 절반만큼 내용을 내려 그렸다(2026-10-17 KTX 문항 자료 1: 안쪽 표 적힌 높이
                            // 1560, 내용 9000 → 46px 아래로 내려가 「※ 출처」 칸과 겹침). 측정과 같은 식으로 더한다
                            Control::Table(t)
                                if t.common.treat_as_char
                                    && crate::renderer::para_has_no_stored_line_segs(para) =>
                            {
                                let para_max_lh =
                                    para.line_segs.iter().map(|s| s.line_height).max().unwrap_or(0);
                                if para_max_lh >= t.common.height as i32 {
                                    // calc_nested_table_height 는 바깥 여백까지 담는다(합성 줄 = 적힌 높이 + 바깥 여백)
                                    let grown = self.calc_nested_table_height(t, styles)
                                        - hwpunit_to_px(para_max_lh, self.dpi);
                                    if grown > 0.5 {
                                        text_height += grown;
                                    }
                                }
                            }
                            Control::Table(_) => {}
