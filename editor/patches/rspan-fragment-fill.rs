// ==== find ====
        // 렌더링 영역의 행별 y 위치 계산 (0부터 시작)
// ==== replace ====
        // [claude-hwpx rspan-fragment-fill] 병합 칸이 다음 쪽까지 걸쳐 이어지는데 이 조각이 행 경계에서 끝나면, 한/글은 이
        // 조각의 마지막 행을 본문 끝(바깥 아래 여백 앞)까지 빈칸으로 늘려 그린다. 다음 쪽은 그대로 다음 행부터다(2026-10-17
        // linetest2 1쪽: 「도입」 칸이 걸친 3행이 다음 쪽으로 넘어가고 표 끝 괘선이 한/글 1042.5px, rhwp 1020.2px). 쪽 배치는
        // 건드리지 않고 그리기만 늘린다. 한/글이 저장한 쪽 배치를 따르는 HWP5 원본과 칸 안 표는 제외
        if enclosing_cell_ctx.is_none()
            && !self.profile.get().hwp5_stored_pagination_layout()
            && end_row < row_count
            && end_cut.is_empty()
            && start_row < end_row
            && table.cells.iter().any(|c| {
                c.row_span > 1
                    && (c.row as usize) < end_row
                    && (c.row as usize) + (c.row_span as usize) > end_row
            })
        {
            let used: f64 = render_rows.iter().map(|&r| row_heights[r]).sum::<f64>()
                + cell_spacing * render_rows.len().saturating_sub(1) as f64;
            let target_bottom = col_area.y + col_area.height
                - hwpunit_to_px(table.outer_margin_bottom as i32, self.dpi);
            let extra = target_bottom - (y_start + used);
            if extra > 0.0 && extra < col_area.height * 0.25 {
                if let Some(&last) = render_rows.last() {
                    row_heights[last] += extra;
                }
            }
        }
        // 렌더링 영역의 행별 y 위치 계산 (0부터 시작)
