// ==== find ====
                    let frags = self.nested_table_mixed_fragment_heights(nt, styles);
// ==== replace ====
                    // [claude-hwpx cell-nested-split] 바깥 표와 자식 표가 모두 「셀 단위로 나눔」(HWPX CELL, 모델 RowBreak)이면
                    // 한/글은 한 쪽보다 작은 1×1 자식 표도 쪽 끝에서 나눈다(한국문화 1단원 사본 실험).
                    // 그 조각은 그리기와 같은 자식 칸 CellUnit 으로 잰다
                    let cell_split_child = self.profile.get().hwpx_container()
                        && matches!(table.page_break, TablePageBreak::RowBreak)
                        && matches!(nt.page_break, TablePageBreak::RowBreak)
                        && !table.common.treat_as_char
                        && !nt.common.treat_as_char;
                    let frags = cell_split_child
                        .then(|| self.claude_child_cell_unit_fragments(nt, styles))
                        .flatten()
                        .unwrap_or_else(|| self.nested_table_mixed_fragment_heights(nt, styles));
// ==== next ====
    fn nested_table_mixed_fragment_heights(
// ==== replace ====
    /// [claude-hwpx cell-nested-split] 1×1 자식 표 칸의 CellUnit 을 부모 조각으로 옮긴다(direct HWPX 투영과 같은 꼴, 재귀 아님).
    fn claude_child_cell_unit_fragments(
        &self,
        table: &crate::model::table::Table,
        styles: &ResolvedStyleSet,
    ) -> Option<Vec<NestedFlowFragment>> {
        if table.row_count != 1 {
            return None;
        }
        let mut cells = table.cells.iter().filter(|cell| cell.row == 0 && cell.row_span == 1);
        let (Some(cell), None) = (cells.next(), cells.next()) else {
            return None;
        };
        let units = self.cell_units(cell, table, styles);
        Some(
            units
                .iter()
                .map(|unit| {
                    let visible = Self::cell_unit_has_visible_content(cell, unit);
                    NestedFlowFragment {
                        height: unit.height,
                        hard_break_before: false,
                        stored_frame_break_before: false,
                        trailing: unit.mixed_nested_trailing || !visible,
                        content_height: if unit.mixed_nested_content_height > 0.0 {
                            unit.mixed_nested_content_height
                        } else if visible {
                            unit.height
                        } else {
                            0.0
                        },
                        recursive: false,
                        starts_after_table: unit.mixed_nested_starts_after_table,
                        source_para_idx: Some(unit.para_idx),
                        recursive_block_prelude_role: RecursiveBlockPreludeRole::None,
                    }
                })
                .collect(),
        )
    }

    fn nested_table_mixed_fragment_heights(
// ==== next ====
                        if anchored_hosted_content_fits {
// ==== replace ====
                        // [claude-hwpx cell-nested-split] 앞 문단에 줄 배치가 없으면 흐름보다 위로 되돌아가는 저장 vpos 는 낡은 값이다
                        let stale_backward_anchor = self.profile.get().hwpx_container()
                            && anchored_y - spacing_before + 0.5 < para_y
                            && cell.paragraphs[..cp_idx]
                                .iter()
                                .any(crate::renderer::para_has_no_stored_line_segs);
                        if anchored_hosted_content_fits && !stale_backward_anchor {
// ==== next ====
            let legacy_single_cell_empty_spacer = is_block_rowbreak
                && table.row_count == 1
                && table.col_count == 1
                && is_empty_spacer_para
// ==== replace ====
            let legacy_single_cell_empty_spacer = is_block_rowbreak
                && table.row_count == 1
                && table.col_count == 1
                && is_empty_spacer_para
                // [claude-hwpx cell-nested-split] 줄 배치 없는 HWPX 빈 문단은 접지 않는다(한/글은 한 줄로 조판)
                && !(self.profile.get().hwpx_container()
                    && crate::renderer::para_has_no_stored_line_segs(p))
// ==== next ====
        let compensate_first_visible = recursive_cut.is_none()
            && offset > 0.5
// ==== replace ====
        // [claude-hwpx cell-nested-split] CellUnit 조각(바깥과 자식 모두 RowBreak, HWPX)은 컷이 정확해 한 줄 건너뛰기 보정을 하지 않는다
        let claude_cell_split_child = self.profile.get().hwpx_container()
            && matches!(table.page_break, TablePageBreak::RowBreak)
            && !table.common.treat_as_char
            && nested.is_some_and(|child| {
                child.row_count == 1
                    && matches!(child.page_break, TablePageBreak::RowBreak)
                    && !child.common.treat_as_char
            });
        let compensate_first_visible = recursive_cut.is_none()
            && !claude_cell_split_child
            && offset > 0.5
// ==== next ====
    pub(crate) fn row_cut_content_height(
// ==== replace ====
    /// [claude-hwpx cell-nested-split] 이 문단이 품은 1×1 자식 표와 바깥 표가 모두 RowBreak(HWPX CELL)인가 — CellUnit 조각 경로
    fn claude_cell_split_host(
        &self,
        table: &crate::model::table::Table,
        para: Option<&crate::model::paragraph::Paragraph>,
    ) -> bool {
        self.profile.get().hwpx_container()
            && matches!(table.page_break, TablePageBreak::RowBreak)
            && !table.common.treat_as_char
            && para.is_some_and(|p| {
                p.controls.iter().any(|control| {
                    matches!(control, Control::Table(child)
                        if child.row_count == 1
                            && matches!(child.page_break, TablePageBreak::RowBreak)
                            && !child.common.treat_as_char)
                })
            })
    }

    pub(crate) fn row_cut_content_height(
// ==== next ====
                    if frags.len() > 1
                        && (total_frag_h > multi_page_px
                            || exceeds_physical_page
                            || native_short_parent_child_fragment
                            || stored_frame_tail_before_next_para)
// ==== replace ====
                    if frags.len() > 1
                        && (total_frag_h > multi_page_px
                            || exceeds_physical_page
                            || native_short_parent_child_fragment
                            || stored_frame_tail_before_next_para
                            || cell_split_child)
// ==== next ====
        } else if self.profile.get().hwpx_stored_layout()
            && terminal
            && offset > 0.5
            && !first_visible_starts_after_table
// ==== replace ====
        } else if self.profile.get().hwpx_stored_layout()
            && !claude_cell_split_child
            && terminal
            && offset > 0.5
            && !first_visible_starts_after_table
// ==== next ====
        let terminal_single_cell_tail = recursive_cut.is_none()
            && terminal
// ==== replace ====
        let terminal_single_cell_tail = recursive_cut.is_none()
            && !claude_cell_split_child
            && terminal
// ==== next ====
        } else if is_offset_continuation && !compensate_first_visible {
            // Mixed text+nested-table units include a small layout allowance
// ==== replace ====
        } else if is_offset_continuation && !compensate_first_visible && !claude_cell_split_child {
            // Mixed text+nested-table units include a small layout allowance
// ==== next ====
        } else if is_offset_continuation && !compensate_first_visible {
            flow_visible + first_visible_content_height
// ==== replace ====
        } else if is_offset_continuation && !compensate_first_visible && !claude_cell_split_child {
            flow_visible + first_visible_content_height
// ==== next ====
                } else if terminal && single_cell_nested_continuation {
// ==== replace ====
                } else if terminal
                    && single_cell_nested_continuation
                    && !self.claude_cell_split_host(table, cell.paragraphs.get(para_idx))
                {
