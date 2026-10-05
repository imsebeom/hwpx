// ==== find ====
                                        let include_trailing_ls = !is_cell_last_line
                                            || (cell_para_count > 1 && table.common.treat_as_char);
// ==== replace ====
                                        // [claude-hwpx cell-trailing-ls-synth] 한/글 줄 기록이 없는 문단(생성기 산출물, 양식 채움)은
                                        // 글자처럼 취급 표의 여러 문단 칸에서도 칸 마지막 줄의 줄 간격을 빼고 잰다. 한/글 2024 PDF 실측
                                        // (2026-10-06 문항카드 채점 기준표): 행마다 줄 간격 하나(4.4~8px)씩 커서 표가 72px 길었다.
                                        // 저장 줄 기록이 있는 문단은 종전 예외(#874/#1086)를 그대로 둔다.
                                        let include_trailing_ls = !is_cell_last_line
                                            || (cell_para_count > 1
                                                && table.common.treat_as_char
                                                && !crate::renderer::para_has_no_stored_line_segs(p));
