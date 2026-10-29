// ==== find ====
        let mut row_y = vec![0.0f64; row_count + 1];
        for i in 0..row_count {
            row_y[i + 1] =
                row_y[i] + row_heights[i] + if i + 1 < row_count { cell_spacing } else { 0.0 };
        }
// ==== replace ====
        let mut row_y = vec![0.0f64; row_count + 1];
        // [claude-hwpx cellspacing-edge] HWPX 는 칸 간격을 표 위아래 끝에도 둔다(결과보고서 124번 표: 높이 = 행 합 + 간격 × (행 수 + 1))
        let claude_edge = self.profile.get().hwpx_container() && cell_spacing > 0.0;
        if claude_edge {
            row_y[0] = cell_spacing;
        }
        for i in 0..row_count {
            row_y[i + 1] = row_y[i]
                + row_heights[i]
                + if i + 1 < row_count || claude_edge { cell_spacing } else { 0.0 };
        }
