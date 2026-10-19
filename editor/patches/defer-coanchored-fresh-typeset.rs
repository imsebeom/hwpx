// ==== find ====
            if std::env::var("RHWP_FLOW_DBG").is_ok() {
// ==== replace ====
            // [claude-hwpx defer-coanchored-fresh] 미룬 공동 앵커 표는 새 쪽 맨 위에 놓는다 — 쪽이 비었거나 이 문단이 쪽 나누기면(먼저 넘긴 뒤)
            if st.profile.hwpx_container() && !st.deferred_table_controls.is_empty() {
                let claude_forced_break = matches!(
                    para.column_type,
                    ColumnBreakType::Page | ColumnBreakType::Section
                );
                // 첫 줄(위 간격 포함)이 남은 자리에 안 들어가도 새 쪽을 열고 미룬 표부터 놓는다(사본 실험: 글 12 보다 체육과 표가 먼저)
                let claude_first_need = para
                    .line_segs
                    .first()
                    .map(|s| hwpunit_to_px(s.line_height, self.dpi))
                    .unwrap_or(0.0)
                    + styles
                        .para_styles
                        .get(para.para_shape_id as usize)
                        .map(|ps| ps.spacing_before.max(0.0))
                        .unwrap_or(0.0);
                let claude_first_overflows =
                    st.current_height + claude_first_need > st.available_height() + 0.01;
                if (claude_forced_break || claude_first_overflows) && !st.current_items.is_empty() {
                    st.advance_column_or_new_page();
                }
                if st.current_items.is_empty() {
                    self.flush_deferred_table_controls(
                        &mut st,
                        paragraphs,
                        composed,
                        styles,
                        measured_tables,
                        None,
                    );
                }
            }
            if std::env::var("RHWP_FLOW_DBG").is_ok() {
// ==== next ====
                        let pages_before_block_table = st.pages.len();
// ==== replace ====
                        // [claude-hwpx defer-coanchored-fresh] 같은 문단 뒤쪽 공동 앵커 표가 남은 자리에 안 들어가고 새 쪽에는 들어가면 미룬다(d322 p77 체육과 표)
                        if st.profile.hwpx_container()
                            && st.col_count == 1
                            && order_pos > 0
                            && !st.current_items.is_empty()
                            && self.is_deferred_coanchored_rowbreak_table(para, table, &fmt)
                            && {
                                let claude_h = ft.effective_height + ft.host_spacing.before;
                                claude_h > st.available_height() - st.current_height
                                    && claude_h <= st.base_available_height()
                            }
                        {
                            st.deferred_table_controls.push(DeferredTableControl {
                                para_index: para_idx,
                                control_index: ctrl_idx,
                                is_first_placed,
                                is_last_placed,
                                para_start_height,
                            });
                            continue;
                        }
                        let pages_before_block_table = st.pages.len();
