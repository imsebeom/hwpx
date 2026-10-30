// ==== find ====
        if table.common.treat_as_char && self.profile.get().hwpx_container() {
            return;
        }
        let target_height = if table.common.height > 0 {
// ==== replace ====
        // [claude-hwpx dummy-cell-grow] 칸 문단 줄 위치가 모두 0 인 더미 줄 배치(생성기) 칸이 있으면 선언대로 키운다(서식2 c52 1×1 표: 한/글이 크게 그림)
        let claude_dummy_cells = table.cells.iter().any(|c| {
            c.paragraphs.len() >= 2
                && c.paragraphs.iter().all(|p| p.line_segs.first().is_some_and(|s| s.vertical_pos == 0))
        });
        // 칸 선언이 내용과 맞으면(모든 열 칸 높이 합이 같고 행 합도 같음) 표 높이가 그보다 큰 몫은 한/글이 그린다(c22: 7704 > 7604)
        let claude_decl_consistent = {
            let ncol = table.cells.iter().map(|c| c.col as usize + c.col_span as usize).max().unwrap_or(0);
            let sums: Vec<i64> = (0..ncol)
                .map(|k| {
                    table
                        .cells
                        .iter()
                        .filter(|c| (c.col as usize) <= k && k < c.col as usize + c.col_span as usize)
                        .map(|c| i64::from(c.height.min(i32::MAX as u32)))
                        .sum()
                })
                .collect();
            let rows_hu = i64::from(crate::renderer::px_to_hwpunit(row_heights.iter().sum::<f64>(), self.dpi));
            !sums.is_empty() && sums.iter().all(|s| *s == sums[0]) && (rows_hu - sums[0]).abs() <= 75
        };
        if table.common.treat_as_char && self.profile.get().hwpx_container() && !claude_dummy_cells && !claude_decl_consistent {
            return;
        }
        let target_height = if table.common.height > 0 {
