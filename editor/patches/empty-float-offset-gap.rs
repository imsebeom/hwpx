// ==== find ====
                let suppress_empty_anchor_spacing =
                    is_current_empty_para_float && !next_is_empty_topbottom_table_anchor;
// ==== replace ====
                // [claude-hwpx empty-float-offset-gap] 저장 줄 배치가 없는 빈 문단의 표 하나는 empty-float-offset-flow 가
                // 한/글 공식(오프셋 + 위 여백 + 표 + 아래 여백)대로 흐름을 정했다. 다음도 빈 문단 표일 때 남기는 표-표 줄 간격
                // (#1133, 저장 사다리 근거)을 또 더하면 그만큼 아래로 밀린다(2026-10-17 교과 평가계획 2쪽 8px — 한/글 재저장본
                // p15 → p16 vpos 차이 23724 = 375+283+22783+283, 줄 간격 없음)
                let suppress_empty_anchor_spacing = is_current_empty_para_float
                    && (!next_is_empty_topbottom_table_anchor
                        || (is_current_empty_topbottom_float
                            && crate::renderer::para_has_no_stored_line_segs(para)
                            && para
                                .controls
                                .iter()
                                .filter(|control| matches!(control, Control::Table(_)))
                                .count()
                                == 1));
