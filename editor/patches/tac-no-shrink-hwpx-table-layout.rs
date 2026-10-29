// ==== find ====
                            let include_trailing_ls = !is_cell_last_line
                                || (para_count > 1 && table.common.treat_as_char);
// ==== replace ====
                            // [claude-hwpx tac-no-shrink-hwpx] HWPX 는 여러 문단 칸도 마지막 줄 뒤 간격 제외(측정과 같은 회계)
                            let include_trailing_ls = !is_cell_last_line
                                || (para_count > 1
                                    && table.common.treat_as_char
                                    && (self.profile.get().native_hwp5_layout() || self.profile.get().hwp3_layout()));
