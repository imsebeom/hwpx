// ==== find ====
                    saved_table_bounds_fit_at_flow_tail(
                        bounds,
                        st.current_height,
                        available,
                        saved_tac_table_frame_height,
                    )
                });
        // [#3837] 저장 vpos 되돌아감은
// ==== replace ====
                    saved_table_bounds_fit_at_flow_tail(
                        bounds,
                        st.current_height,
                        // [claude-hwpx tac-note-stored] 저장 줄이 이 쪽에 표를 두면 각주 몫을 빼지 않고 맞춘다. 각주만 다음 쪽으로 간다(d021, 표 5쪽, 각주 6쪽)
                        st.available_height(),
                        saved_tac_table_frame_height,
                    )
                });
        // [#3837] 저장 vpos 되돌아감은
// ==== next ====
    claude_carry_notes: Vec<(crate::renderer::pagination::FootnoteRef, f64)>,
// ==== replace ====
    claude_carry_notes: Vec<(crate::renderer::pagination::FootnoteRef, f64)>,
    /// [claude-hwpx carry-empty-page] 다음 문단 첫 줄의 저장 위치
    claude_next_first_vpos: Option<i32>,
// ==== next ====
                    if st.profile.hwpx_container() && !st.claude_carry_notes.is_empty() {
                        st.advance_column_or_new_page();
                    }
// ==== replace ====
                    // [claude-hwpx carry-empty-page] 다음 문단의 저장 위치가 0 이면 그 문단이 쪽을 넘긴다. 여기서도 넘기면 각주만 든 쪽이 생긴다(d021, d331)
                    if st.profile.hwpx_container()
                        && !st.claude_carry_notes.is_empty()
                        && st.claude_next_first_vpos != Some(0)
                    {
                        st.advance_column_or_new_page();
                    }
// ==== next ====
            claude_carry_notes: Vec::new(),
// ==== replace ====
            claude_carry_notes: Vec::new(),
            claude_next_first_vpos: None,
// ==== next ====
                self.typeset_table_paragraph(
                    &mut st,
// ==== replace ====
                st.claude_next_first_vpos = paragraphs.get(para_idx + 1).and_then(|n| n.line_segs.first()).map(|s| s.vertical_pos);
                self.typeset_table_paragraph(
                    &mut st,
