// ==== find ====
        let raw_table_height: f64 =
            row_heights.iter().sum::<f64>() + cell_spacing * (row_count.saturating_sub(1) as f64);
// ==== replace ====
        let raw_table_height: f64 =
            row_heights.iter().sum::<f64>() + cell_spacing * (row_count.saturating_sub(1) as f64)
            // [claude-hwpx cellspacing-edge] HWPX 는 칸 간격을 표 위아래 끝에도 둔다
                + if !self.is_native_hwp5 && !self.is_hwp3_variant { cell_spacing * 2.0 } else { 0.0 };
