// ==== find ====
        let table_height = if table.common.treat_as_char
            && common_h > 0.0
            && raw_table_height > common_h + shrink_threshold
// ==== replace ====
        // [claude-hwpx tac-no-ls-shrink] rhwp#7419 — 생성기가 쓴 표(저장 LINE_SEG 가 하나도 없고,
        // 표 선언높이가 행별 셀 선언높이의 합과 같다)는 선언높이가 독립된 측정이 아니라 셀 선언을
        // 다시 적은 값이다. 내용이 그보다 크면 한글은 행을 키운다(재현: 셀 2400+2400, 표 4800 →
        // 한글 재저장 5284, 행 32.0+38.5px). 여기서 줄이면 두 줄이 한 줄 칸에 눌려 아래 표와 겹친다.
        let generator_restated_height = !self.is_native_hwp5
            && table.cells.iter().all(|c| {
                c.paragraphs.iter().all(crate::renderer::para_has_no_stored_line_segs)
            })
            && {
                let rows = table.row_count as usize;
                let declared: Vec<f64> = (0..rows)
                    .map(|r| {
                        table
                            .cells
                            .iter()
                            .filter(|c| c.row as usize == r && c.row_span == 1)
                            .map(|c| hwpunit_to_px(c.height as i32, self.dpi))
                            .fold(0.0f64, f64::max)
                    })
                    .collect();
                declared.iter().all(|h| *h > 0.0)
                    && (declared.iter().sum::<f64>()
                        + cell_spacing * rows.saturating_sub(1) as f64
                        - common_h)
                        .abs()
                        <= 0.5
            };
        let table_height = if table.common.treat_as_char
            && !generator_restated_height
            && common_h > 0.0
            && raw_table_height > common_h + shrink_threshold