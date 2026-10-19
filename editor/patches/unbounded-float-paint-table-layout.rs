// ==== find ====
                            || (signed_hwpunit(table.common.vertical_offset) == 0
                                && clamped < y_start - 0.5
                                && y_start <= body_bottom + table_height + 0.5
                                && y_start + table_height <= page_h_approx + 0.5))
// ==== replace ====
                            || (signed_hwpunit(table.common.vertical_offset) == 0
                                && clamped < y_start - 0.5
                                && y_start <= body_bottom + table_height + 0.5
                                // [claude-hwpx unbounded-float-paint] 나누지 않음 + flowWithText=0 표는 한/글이 용지 밖까지 넘쳐 둔다(조판 unbounded-float-table 과 같은 조건)
                                && (y_start + table_height <= page_h_approx + 0.5
                                    || (self.profile.get().hwpx_container()
                                        && !table.common.treat_as_char
                                        && !table.common.flow_with_text
                                        && matches!(table.page_break, TablePageBreak::None)))))
