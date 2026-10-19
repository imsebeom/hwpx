// ==== find ====
                        // [claude-hwpx defer-coanchored-fresh] 같은 문단 뒤쪽 공동 앵커 표가 남은 자리에 안 들어가고 새 쪽에는 들어가면 미룬다(d322 p77 체육과 표)
// ==== replace ====
                        // [claude-hwpx restrict-float-defer] 쪽 영역 제한 + 나누지 않음 빈 문단 표 하나가 남은 자리에 안 들어가면 미루고 앵커 줄만 이 쪽에 남긴다(한/글 실측, 가이드북 3장 그림 3-2)
                        if st.profile.hwpx_container()
                            && st.col_count == 1
                            && order_pos == 0
                            && !st.current_items.is_empty()
                            && self.claude_is_restrict_float_defer_table(para, table, &fmt)
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
                            st.current_height += para
                                .line_segs
                                .first()
                                .map(|s| hwpunit_to_px(s.line_height + s.line_spacing.max(0), self.dpi))
                                .unwrap_or(0.0);
                            continue;
                        }
                        // [claude-hwpx defer-coanchored-fresh] 같은 문단 뒤쪽 공동 앵커 표가 남은 자리에 안 들어가고 새 쪽에는 들어가면 미룬다(d322 p77 체육과 표)
// ==== next ====
    fn is_coanchored_rowbreak_split_trigger_table(
// ==== replace ====
    /// [claude-hwpx restrict-float-defer] 미룰 수 있는 쪽 영역 제한 표: 글 없는 문단의 유일한 개체, 문단 기준 위아래 배치, 나누지 않음, 오프셋 0
    fn claude_is_restrict_float_defer_table(
        &self,
        para: &Paragraph,
        table: &crate::model::table::Table,
        fmt: &FormattedParagraph,
    ) -> bool {
        use crate::model::shape::{TextWrap, VertRelTo};

        self.profile.get().hwpx_container()
            && !para_has_visible_text(para)
            && para
                .controls
                .iter()
                .filter(|c| matches!(c, Control::Table(_) | Control::Picture(_) | Control::Shape(_)))
                .count()
                == 1
            && !self.is_effective_tac_table(para, table, fmt)
            && !table.common.treat_as_char
            && table.common.flow_with_text
            && matches!(table.common.text_wrap, TextWrap::TopAndBottom)
            && matches!(table.common.vert_rel_to, VertRelTo::Para)
            && matches!(table.page_break, crate::model::table::TablePageBreak::None)
            && signed_hwpunit(table.common.vertical_offset) == 0
    }

    fn is_coanchored_rowbreak_split_trigger_table(
// ==== next ====
            if !self.is_deferred_coanchored_rowbreak_table(para, table, &fmt) {
                continue;
            }
// ==== replace ====
            // [claude-hwpx restrict-float-defer] 쪽 영역 제한 표도 꺼낸다
            if !self.is_deferred_coanchored_rowbreak_table(para, table, &fmt)
                && !self.claude_is_restrict_float_defer_table(para, table, &fmt)
            {
                continue;
            }
// ==== next ====
        styles: &ResolvedStyleSet,
        is_last_in_section: bool,
    ) {
        // [#2243 진단] 문단 진입 시 누적 높이
// ==== replace ====
        styles: &ResolvedStyleSet,
        is_last_in_section: bool,
        // [claude-hwpx restrict-float-defer] 글 문단이 쪽을 넘길 때 미룬 표를 꺼내려고 받는다
        claude_composed: &[ComposedParagraph],
        claude_measured: &[MeasuredTable],
    ) {
        // [#2243 진단] 문단 진입 시 누적 높이
// ==== next ====
                    &formatted,
                    paragraphs,
                    styles,
                    is_last_in_section,
                );
// ==== replace ====
                    &formatted,
                    paragraphs,
                    styles,
                    is_last_in_section,
                    composed, // [claude-hwpx restrict-float-defer]
                    measured_tables,
                );
// ==== next ====
            && !hwp_first_line_before_reset_fits
        {
            st.advance_column_or_new_page();
        }
// ==== replace ====
            && !hwp_first_line_before_reset_fits
        {
            st.advance_column_or_new_page();
            // [claude-hwpx restrict-float-defer] 새 쪽 맨 위에 미룬 표부터
            if st.profile.hwpx_container()
                && !st.deferred_table_controls.is_empty()
                && st.current_items.is_empty()
            {
                self.flush_deferred_table_controls(st, paragraphs, claude_composed, styles, claude_measured, None);
            }
        }
// ==== next ====
                {
                    st.advance_column_or_new_page();
                    continue;
                }
                st.current_items.push(PageItem::FullParagraph {
// ==== replace ====
                {
                    st.advance_column_or_new_page();
                    // [claude-hwpx restrict-float-defer] 새 쪽 맨 위에 미룬 표부터
                    if st.profile.hwpx_container()
                        && !st.deferred_table_controls.is_empty()
                        && st.current_items.is_empty()
                    {
                        self.flush_deferred_table_controls(st, paragraphs, claude_composed, styles, claude_measured, None);
                    }
                    continue;
                }
                st.current_items.push(PageItem::FullParagraph {
// ==== next ====
            // move: 나머지 줄 → 다음 단/페이지
            st.advance_column_or_new_page();
            cursor_line = end_line;
// ==== replace ====
            // move: 나머지 줄 → 다음 단/페이지
            st.advance_column_or_new_page();
            // [claude-hwpx restrict-float-defer] 3쪽에서 시작한 문단의 나머지 줄은 4쪽의 미룬 표 아래에서 잇는다(한/글 실측)
            if st.profile.hwpx_container()
                && !st.deferred_table_controls.is_empty()
                && st.current_items.is_empty()
            {
                self.flush_deferred_table_controls(st, paragraphs, claude_composed, styles, claude_measured, None);
            }
            cursor_line = end_line;
// ==== next ====
                    .max(0.0)
            } else {
                base_available
            };
// ==== replace ====
                    .max(0.0)
            } else if st.profile.hwpx_container()
                && st.current_height > 0.0
                && matches!(st.current_items.first(), Some(PageItem::Table { .. } | PageItem::PartialTable { .. }))
            {
                // [claude-hwpx restrict-float-defer] 이어지는 줄 앞에 미룬 표를 놓았으면 그 높이와 각주 자리를 뺀다
                (base_available - st.current_footnote_height - fn_margin - st.current_height).max(0.0)
            } else {
                base_available
            };
// ==== next ====
                    if self.is_effective_tac_table(para, table, &fmt) {
// ==== replace ====
                    // [claude-hwpx restrict-float-defer] 미룬 표가 있고 이 표(글자처럼 취급이거나 나누지 않음)가 남은 자리에 안 들어가 새 쪽으로 가면
                    // 새 쪽에 미룬 표부터 놓는다(한/글 실측: 2-4 원고 사본, 그림 4-6 다음 「예시 프롬프트」 상자)
                    if st.profile.hwpx_container()
                        && st.col_count == 1
                        && !st.deferred_table_controls.is_empty()
                        && st.deferred_table_controls.iter().all(|d| d.para_index < para_idx)
                        && (self.is_effective_tac_table(para, table, &fmt)
                            || matches!(table.page_break, crate::model::table::TablePageBreak::None))
                    {
                        let claude_h = ft.effective_height + ft.host_spacing.before;
                        // 표 문단이 이미 새 쪽으로 넘어왔으면 바로, 아니면 이 표가 안 들어갈 때 쪽을 넘기고 꺼낸다
                        if !st.current_items.is_empty()
                            && claude_h > st.available_height() - st.current_height
                            && claude_h <= st.base_available_height()
                        {
                            st.advance_column_or_new_page();
                        }
                        if st.current_items.is_empty() {
                            self.flush_deferred_table_controls(st, paragraphs_all, composed_all, styles, measured_tables, None);
                        }
                    }
                    if self.is_effective_tac_table(para, table, &fmt) {
// ==== next ====
        let strict_after_empty_host_float = take_strict_plain_text_fit_after_empty_host_float_once(
// ==== replace ====
        // [claude-hwpx restrict-float-defer] 이 문단 앞에서 쪽이 이미 넘어가 비었으면 미룬 표부터(문단 시작 훅 뒤에 넘기는 규칙이 있다, 2-4 사본 p58)
        if st.profile.hwpx_container()
            && !st.deferred_table_controls.is_empty()
            && st.current_items.is_empty()
        {
            self.flush_deferred_table_controls(st, paragraphs, claude_composed, styles, claude_measured, None);
        }
        let strict_after_empty_host_float = take_strict_plain_text_fit_after_empty_host_float_once(
