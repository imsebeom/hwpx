// ==== find ====
        // 3단계: 높이가 0인 행은 기본값 적용
        for h in &mut row_heights {
            if *h <= 0.0 {
                *h = hwpunit_to_px(400, self.dpi);
            }
        }
// ==== replace ====
        // 3단계: 높이가 0인 행은 기본값 적용
        // [claude-hwpx zero-span-row] HWPX 는 병합 칸에만 걸친 행(한 행 칸 없음)이 선언으로 0 이 되면 0 으로 둔다(d120 예산표: 한/글 행 합 = 표 높이)
        let claude_hwpx = !self.is_native_hwp5 && !self.is_hwp3_variant;
        for (r, h) in row_heights.iter_mut().enumerate() {
            if *h <= 0.0 {
                let span_only = claude_hwpx
                    && !table.cells.iter().any(|c| c.row as usize == r && c.row_span == 1)
                    && table.cells.iter().any(|c| {
                        c.row_span > 1 && (c.row as usize) <= r && r < c.row as usize + c.row_span as usize
                    });
                if !span_only {
                    *h = hwpunit_to_px(400, self.dpi);
                }
            }
        }
