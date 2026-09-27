    /// [claude-hwpx tac-host-sync] 편집한 표 하나의 높이를 잰다(캡션 제외 전 값, px).
    pub fn measure_table_for_edit(
        &self,
        table: &Table,
        para_index: usize,
        control_index: usize,
        styles: &ResolvedStyleSet,
    ) -> f64 {
        self.measure_table(table, para_index, control_index, styles)
            .total_height
    }

