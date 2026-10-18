// ==== find ====
    reset_vpos_after_queued_table_footnote_page: bool,
// ==== replace ====
    reset_vpos_after_queued_table_footnote_page: bool,
    /// [claude-hwpx footnote-carry] 이 쪽 아래에 들어가지 않아 다음 쪽 각주 영역 맨 앞으로 넘길 표 칸 각주(각주, 높이)
    claude_carry_notes: Vec<(crate::renderer::pagination::FootnoteRef, f64)>,
// ==== next ====
        self.pages.push(self.new_page_content(Vec::new()));
        self.reset_for_new_page();
// ==== replace ====
        self.pages.push(self.new_page_content(Vec::new()));
        self.reset_for_new_page();
        // [claude-hwpx footnote-carry] 앞 쪽에 들어가지 않아 넘긴 표 칸 각주를 이 쪽 각주 영역 맨 앞에 둔다. 한/글은 넘긴 각주 자리를 이 쪽 본문에서
        // 비우지 않는다(가이드북 2장 7쪽: 본문 줄 981.5, 1003.1 과 각주 줄 969.6~1016.5 가 겹쳐 그려짐) — 쪽 나눔을 맞추려 높이는 예약하지 않는다
        for (note, _height) in std::mem::take(&mut self.claude_carry_notes) {
            if let Some(page) = self.pages.last_mut() {
                page.footnotes.push(note);
            }
        }
// ==== next ====
                let projected =
                    st.projected_footnote_height(ft.table_footnote_height, ft.table_footnote_count);
                let extra = (projected - reclaim).max(0.0) - (st.current_footnote_height - reclaim).max(0.0);
// ==== replace ====
                // [claude-hwpx footnote-carry] HWPX 는 첫 각주만 들어가면 표를 이 쪽에 두고 나머지 각주는 다음 쪽으로 넘긴다(가이드북 2장 표 2-1)
                let projected = if st.profile.hwpx_container() {
                    let first = ft
                        .table_footnotes
                        .first()
                        .map(|note| note.content_height)
                        .unwrap_or(ft.table_footnote_height);
                    st.projected_footnote_height(first, 1)
                } else {
                    st.projected_footnote_height(ft.table_footnote_height, ft.table_footnote_count)
                };
                let extra = (projected - reclaim).max(0.0) - (st.current_footnote_height - reclaim).max(0.0);
// ==== next ====
                    // 표 셀 내 각주 수집 (Paginator engine.rs:679-701 동일)
                    if !st
                        .fragment_queued_table_footnotes
                        .contains(&(para_idx, ctrl_idx))
                    {
                        for (cell_idx, cell) in table.cells.iter().enumerate() {
                            for (cp_idx, cp) in cell.paragraphs.iter().enumerate() {
                                for (cc_idx, cc) in cp.controls.iter().enumerate() {
                                    if let Control::Footnote(fn_ctrl) = cc {
                                        self.register_unqueued_table_footnote(
                                            st,
                                            fn_ctrl,
                                            FootnoteSource::TableCell {
                                                para_index: para_idx,
                                                table_control_index: ctrl_idx,
                                                cell_index: cell_idx,
                                                cell_para_index: cp_idx,
                                                cell_control_index: cc_idx,
                                            },
                                        );
                                    }
// ==== replace ====
                    // 표 셀 내 각주 수집 (Paginator engine.rs:679-701 동일)
                    if !st
                        .fragment_queued_table_footnotes
                        .contains(&(para_idx, ctrl_idx))
                    {
                        for (cell_idx, cell) in table.cells.iter().enumerate() {
                            for (cp_idx, cp) in cell.paragraphs.iter().enumerate() {
                                for (cc_idx, cc) in cp.controls.iter().enumerate() {
                                    if let Control::Footnote(fn_ctrl) = cc {
                                        let source = FootnoteSource::TableCell {
                                            para_index: para_idx,
                                            table_control_index: ctrl_idx,
                                            cell_index: cell_idx,
                                            cell_para_index: cp_idx,
                                            cell_control_index: cc_idx,
                                        };
                                        // [claude-hwpx footnote-carry] HWPX 단일 단에서 이 쪽 아래에 들어가지 않는 각주(와 그 뒤 각주)는 다음 쪽으로 넘긴다
                                        // 높이는 조판한 줄(줄 높이 + 줄 간격)로 재고, 바닥글 자리는 쓰지 않는다(한/글이 본문 아래 끝까지만 둔다)
                                        let note_h = composed_footnote_content_height(fn_ctrl, self.dpi);
                                        let claude_hwpx_note = st.profile.hwpx_container() && st.col_count == 1;
                                        if claude_hwpx_note
                                            && (!st.claude_carry_notes.is_empty()
                                                || st.current_height + st.projected_footnote_height(note_h, 1)
                                                    > st.base_available_height() - st.current_zone_y_offset + 0.5)
                                        {
                                            st.claude_carry_notes.push((
                                                crate::renderer::pagination::FootnoteRef {
                                                    number: fn_ctrl.number,
                                                    source,
                                                    fragment: None,
                                                },
                                                note_h,
                                            ));
                                            continue;
                                        }
                                        if claude_hwpx_note {
                                            self.register_unqueued_table_footnote_with_content_height(st, fn_ctrl, source, note_h);
                                        } else {
                                            self.register_unqueued_table_footnote(st, fn_ctrl, source);
                                        }
                                    }
// ==== next ====
    fn available_height(&self) -> f64 {
        let base = self.base_available_height();
        let fn_margin = if self.current_footnote_height > 0.0 {
// ==== replace ====
    fn available_height(&self) -> f64 {
        let base = self.base_available_height();
        // [claude-hwpx footnote-carry] HWPX 는 각주 문단 줄을 불러올 때 만들어(footnote-reflow) 각주 높이를 실제로 잰다. 어림 시절의 안전 여유 40px 는
        // 한/글보다 쪽을 일찍 넘긴다(d327: 한/글은 각주 2줄과 구분선을 넣고 0.1px 남기고 마지막 문단을 둔다)
        let fn_margin = if self.current_footnote_height > 0.0 && !self.profile.hwpx_container() {
// ==== next ====
        let footnote_penalty = (self.current_footnote_height - self.footer_band_reclaim()).max(0.0);
// ==== replace ====
        // [claude-hwpx footnote-carry] HWPX 는 각주가 빈 바닥글 띠를 쓰지 않는다(한/글: 가이드북 2장 두 판 모두 각주 영역이 본문 아래 끝 안에 들고
        // 마지막 줄만 약 4px 넘친다). 띠를 빼면 각주 위 본문이 각주와 겹쳤다(2-3 원고 _261012_05 6쪽)
        let footnote_penalty = if self.profile.hwpx_container() {
            self.current_footnote_height
        } else {
            (self.current_footnote_height - self.footer_band_reclaim()).max(0.0)
        };
// ==== next ====
                            let fn_height = estimate_footnote_note_height(fn_ctrl, self.dpi);
// ==== replace ====
                            // [claude-hwpx footnote-carry] HWPX 본문 각주도 조판한 줄(줄 높이 + 줄 간격)로 잰다. 줄 높이만 세면 2줄 각주가 24px(실제 31.2px)로
                            // 잡혀 한/글보다 한 줄을 더 담고 각주와 겹쳤다(가이드북 3장 2쪽 각주 6, 7)
                            let fn_height = if st.profile.hwpx_container() {
                                composed_footnote_content_height(fn_ctrl, self.dpi)
                            } else {
                                estimate_footnote_note_height(fn_ctrl, self.dpi)
                            };
// ==== next ====
                    if break_after_current_table {
// ==== replace ====
                    // [claude-hwpx footnote-carry] 각주를 다음 쪽으로 넘겼으면 이 쪽은 찼다. 뒤 흐름은 다음 쪽에서 시작한다(한/글: 표 2-1 캡션이 7쪽 머리)
                    if st.profile.hwpx_container() && !st.claude_carry_notes.is_empty() {
                        st.advance_column_or_new_page();
                    }
                    if break_after_current_table {
// ==== next ====
            reset_vpos_after_queued_table_footnote_page: false,
// ==== replace ====
            reset_vpos_after_queued_table_footnote_page: false,
            claude_carry_notes: Vec::new(),
