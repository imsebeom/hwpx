// ==== find ====
                                        let include_trailing_ls = !is_cell_last_line
                                            || (cell_para_count > 1
                                                && table.common.treat_as_char
                                                && !crate::renderer::para_has_no_stored_line_segs(p));
                                        if include_trailing_ls {
                                            let trailing =
                                                hwpunit_to_px(line.line_spacing, self.dpi);
                                            // [#6030] TAC 다문단 예외로 포함되는 셀 마지막
                                            // 줄의 trailing 이 음수(압축 줄간격, 70% 등)면
                                            // 0 으로 — 뒤에 줄이 없어 압축 대상이 없고,
                                            // 한글은 마지막 글리프 박스를 lh 그대로 그려
                                            // 행을 그만큼 키운다(2386771 심사서식 10곳
                                            // descender 깎임). 양수 trailing 포함 회계
                                            // (KTX TOC 핀)는 불변.
                                            let trailing = if is_cell_last_line {
                                                trailing.max(0.0)
                                            } else {
                                                trailing
                                            };
                                            h + trailing
                                        } else {
                                            h
                                        }
                                    })
                                    .enumerate()
                                    // [#6299] 앞 줄의 가로 조각은 높이를 다시 더하지 않는다.
                                    .filter(|(i, _)| !stored_seg_is_row_fragment(p, *i))
                                    .map(|(_, h)| h)
                                    .sum();
                                spacing_before + lines_total + spacing_after
                            }
                        })
                        .sum()
                };
                // 중첩 표가 있는 셀: LINE_SEG.line_height에 중첩 표 높이가 미포함.
// ==== replace ====
                                        // [claude-hwpx tac-no-shrink-hwpx] HWPX 는 여러 문단 칸도 마지막 줄 뒤 간격을 빼고 잰다(결과보고서 158번 표:
                                        // 한/글 행 = 저장 줄 끝 43.3 + 여백 3.8, 엔진은 간격 272 를 더해 3.6px 컸다). #874/#1086 예외는 HWP5, HWP3 만
                                        let include_trailing_ls = !is_cell_last_line
                                            || (cell_para_count > 1
                                                && (self.is_native_hwp5 || self.is_hwp3_variant)
                                                && table.common.treat_as_char
                                                && !crate::renderer::para_has_no_stored_line_segs(p));
                                        if include_trailing_ls {
                                            let trailing =
                                                hwpunit_to_px(line.line_spacing, self.dpi);
                                            // [#6030] TAC 다문단 예외로 포함되는 셀 마지막
                                            // 줄의 trailing 이 음수(압축 줄간격, 70% 등)면
                                            // 0 으로 — 뒤에 줄이 없어 압축 대상이 없고,
                                            // 한글은 마지막 글리프 박스를 lh 그대로 그려
                                            // 행을 그만큼 키운다(2386771 심사서식 10곳
                                            // descender 깎임). 양수 trailing 포함 회계
                                            // (KTX TOC 핀)는 불변.
                                            let trailing = if is_cell_last_line {
                                                trailing.max(0.0)
                                            } else {
                                                trailing
                                            };
                                            h + trailing
                                        } else {
                                            h
                                        }
                                    })
                                    .enumerate()
                                    // [#6299] 앞 줄의 가로 조각은 높이를 다시 더하지 않는다.
                                    .filter(|(i, _)| !stored_seg_is_row_fragment(p, *i))
                                    .map(|(_, h)| h)
                                    .sum();
                                spacing_before + lines_total + spacing_after
                            }
                        })
                        .sum()
                };
                // 중첩 표가 있는 셀: LINE_SEG.line_height에 중첩 표 높이가 미포함.
// ==== next ====
                                        let include_trailing_ls = !is_cell_last_line
                                            || (cell_para_count > 1
                                                && table.common.treat_as_char
                                                && !crate::renderer::para_has_no_stored_line_segs(p));
                                        if include_trailing_ls {
                                            let trailing =
                                                hwpunit_to_px(line.line_spacing, self.dpi);
                                            // [#6030] TAC 다문단 예외로 포함되는 셀 마지막
                                            // 줄의 trailing 이 음수(압축 줄간격, 70% 등)면
                                            // 0 으로 — 뒤에 줄이 없어 압축 대상이 없고,
                                            // 한글은 마지막 글리프 박스를 lh 그대로 그려
                                            // 행을 그만큼 키운다(2386771 심사서식 10곳
                                            // descender 깎임). 양수 trailing 포함 회계
                                            // (KTX TOC 핀)는 불변.
                                            let trailing = if is_cell_last_line {
                                                trailing.max(0.0)
                                            } else {
                                                trailing
                                            };
                                            h + trailing
                                        } else {
                                            h
                                        }
                                    })
                                    .enumerate()
                                    // [#6299] 앞 줄의 가로 조각은 높이를 다시 더하지 않는다.
                                    .filter(|(i, _)| !stored_seg_is_row_fragment(p, *i))
                                    .map(|(_, h)| h)
                                    .sum();
                                spacing_before + lines_total + spacing_after
                            }
                        })
                        .sum()
                };
                // LINE_SEG의 line_height에 이미 셀 내 중첩 표 높이가 반영되어 있으므로
// ==== replace ====
                                        // [claude-hwpx tac-no-shrink-hwpx] HWPX 는 여러 문단 칸도 마지막 줄 뒤 간격을 빼고 잰다(결과보고서 158번 표:
                                        // 한/글 행 = 저장 줄 끝 43.3 + 여백 3.8, 엔진은 간격 272 를 더해 3.6px 컸다). #874/#1086 예외는 HWP5, HWP3 만
                                        let include_trailing_ls = !is_cell_last_line
                                            || (cell_para_count > 1
                                                && (self.is_native_hwp5 || self.is_hwp3_variant)
                                                && table.common.treat_as_char
                                                && !crate::renderer::para_has_no_stored_line_segs(p));
                                        if include_trailing_ls {
                                            let trailing =
                                                hwpunit_to_px(line.line_spacing, self.dpi);
                                            // [#6030] TAC 다문단 예외로 포함되는 셀 마지막
                                            // 줄의 trailing 이 음수(압축 줄간격, 70% 등)면
                                            // 0 으로 — 뒤에 줄이 없어 압축 대상이 없고,
                                            // 한글은 마지막 글리프 박스를 lh 그대로 그려
                                            // 행을 그만큼 키운다(2386771 심사서식 10곳
                                            // descender 깎임). 양수 trailing 포함 회계
                                            // (KTX TOC 핀)는 불변.
                                            let trailing = if is_cell_last_line {
                                                trailing.max(0.0)
                                            } else {
                                                trailing
                                            };
                                            h + trailing
                                        } else {
                                            h
                                        }
                                    })
                                    .enumerate()
                                    // [#6299] 앞 줄의 가로 조각은 높이를 다시 더하지 않는다.
                                    .filter(|(i, _)| !stored_seg_is_row_fragment(p, *i))
                                    .map(|(_, h)| h)
                                    .sum();
                                spacing_before + lines_total + spacing_after
                            }
                        })
                        .sum()
                };
                // LINE_SEG의 line_height에 이미 셀 내 중첩 표 높이가 반영되어 있으므로
// ==== next ====
        let table_height = if table.common.treat_as_char
            && !generator_restated_height
// ==== replace ====
        // [claude-hwpx tac-no-shrink-hwpx] HWPX 는 한/글이 열 때 표 높이를 행 내용으로 다시 잰다(선언 높이로 누르지 않는다, 결과보고서 159번 표)
        let claude_hwpx_restates = !self.is_native_hwp5 && !self.is_hwp3_variant;
        let table_height = if table.common.treat_as_char
            && !generator_restated_height
            && !claude_hwpx_restates
