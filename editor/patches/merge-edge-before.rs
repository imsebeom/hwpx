// ==== find ====
        let table = self.get_table_mut(section_idx, parent_para_idx, control_idx)?;
        table
            .merge_cells(start_row, start_col, end_row, end_col)
// ==== replace ====
        // [claude-hwpx merge-edge-before] 합치기 전에 오른쪽, 아래 가장자리 셀의 BorderFill 을 기억한다
        let merge_edge_bf: (u16, u16) = {
            let table = self.get_table_mut(section_idx, parent_para_idx, control_idx)?;
            let right = table
                .cells
                .iter()
                .find(|c| c.row == start_row && c.col + c.col_span.max(1) - 1 == end_col)
                .map(|c| c.border_fill_id)
                .unwrap_or(0);
            let bottom = table
                .cells
                .iter()
                .find(|c| c.col == start_col && c.row + c.row_span.max(1) - 1 == end_row)
                .map(|c| c.border_fill_id)
                .unwrap_or(0);
            (right, bottom)
        };
        let table = self.get_table_mut(section_idx, parent_para_idx, control_idx)?;
        table
            .merge_cells(start_row, start_col, end_row, end_col)
