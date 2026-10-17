// ==== find ====
            } else {
                !start_cut.is_empty() && cell_row == start_row
            };
            let is_split_end_row = if is_block_split {
                split_end_block.is_some_and(|(s, e)| cell_row < e && cell_end_row > s)
            } else {
                !end_cut.is_empty() && cell_row == end_row.saturating_sub(1)
            };
            let is_in_split_row = is_split_start_row || is_split_end_row;
            // [#5946]
// ==== replace ====
            } else {
                // [claude-hwpx rowspan-cut-row] 행 단위 자름 표는 그 행의 한 행 칸만 담는다. 병합 칸은 아래 높이 경로가 맡는다
                !start_cut.is_empty() && cell_row == start_row && cell.row_span == 1
            };
            let is_split_end_row = if is_block_split {
                split_end_block.is_some_and(|(s, e)| cell_row < e && cell_end_row > s)
            } else {
                !end_cut.is_empty() && cell_row == end_row.saturating_sub(1) && cell.row_span == 1
            };
            let is_in_split_row = is_split_start_row || is_split_end_row;
            // [#5946]
// ==== next ====
            let straddles_fragment_start = cell_row < start_row && cell_end_row > start_row;
            let straddles_fragment_end
// ==== replace ====
            let straddles_fragment_start = (cell_row < start_row && cell_end_row > start_row)
                // [claude-hwpx rowspan-cut-row] 자르는 행(조각 시작 행)에서 시작하는 병합 칸도 앞 조각에 일부를 그렸다
                || (!is_block_split
                    && cell.row_span > 1
                    && cell_row == start_row
                    && !start_cut.is_empty());
            let straddles_fragment_end
