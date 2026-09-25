        // [claude-hwpx merge-edge-after] 합친 셀에 가장자리 셀의 오른쪽, 아래 선을 입힌다
        {
            let main_bf = self
                .get_table_mut(section_idx, parent_para_idx, control_idx)?
                .cells
                .iter()
                .find(|c| c.row == start_row && c.col == start_col)
                .map(|c| c.border_fill_id)
                .unwrap_or(0);
            let new_bf = self.merged_cell_border_fill(main_bf, merge_edge_bf.0, merge_edge_bf.1);
            if new_bf != main_bf && new_bf > 0 {
                let table = self.get_table_mut(section_idx, parent_para_idx, control_idx)?;
                if let Some(c) = table
                    .cells
                    .iter_mut()
                    .find(|c| c.row == start_row && c.col == start_col)
                {
                    c.border_fill_id = new_bf;
                }
            }
        }

