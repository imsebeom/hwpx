// ==== find ====
                && res.end_cut.iter().any(|units| *units > 0)
                && row_has_stored_same_vpos_split_signal(table, r);
// ==== replace ====
                && res.end_cut.iter().any(|units| *units > 0)
                // [claude-hwpx cell-unit-keep-hwpx] 줄 배치 없는 HWPX 는 저장 흔적이 없어도 완결 줄 하나면 남긴다(한/글 새 조판 d189 p9 둘째 행 첫 줄 16.9px)
                && (row_has_stored_same_vpos_split_signal(table, r)
                    || (st.profile.hwpx_container()
                        && table.cells.iter().filter(|c| c.row as usize == r).all(|c| {
                            c.paragraphs.iter().all(|p| {
                                p.line_segs.iter().all(|s| {
                                    s.tag & crate::model::paragraph::LineSeg::TAG_IMPLEMENTATION_PROPERTY != 0
                                })
                            })
                        })));
