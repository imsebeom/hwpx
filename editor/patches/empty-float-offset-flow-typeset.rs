// ==== find ====
                        .and_then(|(next_vpos, host_vpos)| {
                            crate::renderer::float_placement::empty_host_physical_ladder_extras_hu(
                                table, host_vpos, next_vpos,
                            )
                        })
                })
                .flatten();
// ==== replace ====
                        .and_then(|(next_vpos, host_vpos)| {
                            crate::renderer::float_placement::empty_host_physical_ladder_extras_hu(
                                table, host_vpos, next_vpos,
                            )
                        })
                })
                .flatten()
                // [claude-hwpx empty-float-offset-flow-typeset] 저장 줄 배치가 없는 빈 문단의 위아래 배치 표 하나는 한/글처럼
                // 오프셋과 바깥 여백 위아래를 흐름에 더한다 — layout 의 empty-float-offset-flow 와 짝
                .or_else(|| {
                    (is_para_topbottom_float(&table.common)
                        && !para_has_non_whitespace_text(para)
                        && crate::renderer::para_has_no_stored_line_segs(para)
                        && para
                            .controls
                            .iter()
                            .filter(|control| matches!(control, Control::Table(_)))
                            .count()
                            == 1)
                        .then(|| {
                            i64::from(signed_hwpunit(table.common.vertical_offset).max(0))
                                + i64::from(table.outer_margin_top)
                                + i64::from(table.outer_margin_bottom)
                        })
                        .filter(|extras| *extras > 0)
                });
