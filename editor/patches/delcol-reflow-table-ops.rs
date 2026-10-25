// ==== find ====
        let table = self.get_table_mut(section_idx, parent_para_idx, control_idx)?;
        table
            .delete_column(col_idx)
            .map_err(|e| HwpError::RenderError(e))?;
        table.dirty = true;
        let row_count = table.row_count;
        let col_count = table.col_count;
// ==== replace ====
        let table = self.get_table_mut(section_idx, parent_para_idx, control_idx)?;
        // [claude-hwpx delcol-reflow] 지울 열에 걸친 병합 칸은 남아서 좁아진다. 그 칸 글을 새 폭으로 다시 접는다 — 종전에는
        // 옛 폭의 줄 나눔이 남아 한 줄로 그려졌다(2026-10-25 편집 순서 시험 「병합 → 열 삭제」, 처음부터 조판하면 다섯 줄).
        // 지운 열 앞에서 시작한 칸은 열 번호가 그대로고, 그 열에서 시작한 칸은 다음 열이 당겨와 같은 번호가 된다
        let narrowed: Vec<(u16, u16)> = table
            .cells
            .iter()
            .filter(|c| c.col_span > 1 && c.col <= col_idx && col_idx < c.col + c.col_span)
            .map(|c| (c.row, c.col))
            .collect();
        table
            .delete_column(col_idx)
            .map_err(|e| HwpError::RenderError(e))?;
        table.dirty = true;
        let row_count = table.row_count;
        let col_count = table.col_count;
        // reflow_table_cell_paragraphs 는 (칸 번호, 문단 수) 짝을 받는다
        let narrowed_paras: Vec<(usize, usize)> = table
            .cells
            .iter()
            .enumerate()
            .filter(|(_, c)| narrowed.contains(&(c.row, c.col)))
            .map(|(ci, c)| (ci, c.paragraphs.len()))
            .collect();
// ==== next ====
        self.document.sections[section_idx].raw_stream = None;
        self.recompose_section(section_idx);
        self.paginate_if_needed();

        self.event_log.push(DocumentEvent::TableColumnDeleted {
// ==== replace ====
        self.document.sections[section_idx].raw_stream = None;
        self.recompose_section(section_idx);
        self.paginate_if_needed();

        if !narrowed_paras.is_empty() {
            self.reflow_table_cell_paragraphs(section_idx, parent_para_idx, control_idx, &narrowed_paras);
            self.mark_section_dirty(section_idx);
            self.paginate_if_needed();
        }
        self.event_log.push(DocumentEvent::TableColumnDeleted {
