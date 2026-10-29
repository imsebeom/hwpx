// ==== find ====
                st.vpos_ladder_dirty
                    || !spacing_trim_restorable(paragraphs, para_idx)
                    || (st.vpos_page_base.is_none() && st.vpos_lazy_base.is_none()),
// ==== replace ====
                st.vpos_ladder_dirty
                    || !spacing_trim_restorable(paragraphs, para_idx)
                    || (st.vpos_page_base.is_none() && st.vpos_lazy_base.is_none())
                    // [claude-hwpx tac-flow-no-trim] 다음 문단이 TAC 흐름 표면 그 경로는 저장 위치로 스냅하지 않아 줄인 간격을 되찾지 못한다(결과보고서 228, 232)
                    || (st.profile.hwpx_container()
                        && paragraphs.get(para_idx + 1).is_some_and(|next| {
                            next.controls.iter().any(|c| {
                                matches!(c, Control::Table(t) if t.common.treat_as_char && t.common.flow_with_text)
                            })
                        })),
