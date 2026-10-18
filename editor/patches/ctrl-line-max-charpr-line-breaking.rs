// ==== find ====
            let mut new_line_segs = Vec::with_capacity(line_specs.len());
            for (line_idx, (start_pos, _line_width, height_hwp)) in
                line_specs.into_iter().enumerate()
            {
// ==== replace ====
            let mut new_line_segs = Vec::with_capacity(line_specs.len());
            // [claude-hwpx ctrl-line-max-charpr] 줄마다 다음 줄 시작(마지막 줄은 문단 끝까지)
            let claude_line_ends: Vec<u32> = line_specs.iter().skip(1).map(|spec| spec.0).collect();
            for (line_idx, (start_pos, _line_width, height_hwp)) in
                line_specs.into_iter().enumerate()
            {
// ==== next ====
                let control_font_size = para
                    .char_shapes
                    .iter()
                    .rev()
                    .find(|c| c.start_pos <= start_pos)
                    .or_else(|| para.char_shapes.first())
                    .and_then(|c| styles.char_styles.get(c.char_shape_id as usize))
                    .map(|style| style.font_size)
                    .unwrap_or(0.0);
// ==== replace ====
                let control_font_size = para
                    .char_shapes
                    .iter()
                    .rev()
                    .find(|c| c.start_pos <= start_pos)
                    .or_else(|| para.char_shapes.first())
                    .and_then(|c| styles.char_styles.get(c.char_shape_id as usize))
                    .map(|style| style.font_size)
                    .unwrap_or(0.0);
                // [claude-hwpx ctrl-line-max-charpr] 한/글은 그 줄에 걸친 run(구역 정의만 든 run, 끝 빈 run 포함) 가운데 가장 큰 크기로 셈한다
                // (secpr_engine.py: d001 1900, 1900, 2200 → 간격 1320, d095 끝 빈 run 1500 → 900)
                let line_end = claude_line_ends.get(line_idx).copied().unwrap_or(u32::MAX);
                let control_font_size = para
                    .char_shapes
                    .iter()
                    .filter(|c| c.start_pos >= start_pos && c.start_pos < line_end)
                    .filter_map(|c| styles.char_styles.get(c.char_shape_id as usize))
                    .map(|style| style.font_size)
                    .fold(control_font_size, f64::max);
// ==== next ====
            let font_size = para
                .char_shapes
                .first()
                .and_then(|char_shape| styles.char_styles.get(char_shape.char_shape_id as usize))
                .or_else(|| para.char_shapes.is_empty().then(|| styles.char_styles.first()).flatten())
                .map(|style| style.font_size)
                .unwrap_or(12.0);
// ==== replace ====
            let font_size = para
                .char_shapes
                .first()
                .and_then(|char_shape| styles.char_styles.get(char_shape.char_shape_id as usize))
                .or_else(|| para.char_shapes.is_empty().then(|| styles.char_styles.first()).flatten())
                .map(|style| style.font_size)
                .unwrap_or(12.0);
            // [claude-hwpx ctrl-line-max-charpr] run 이 여럿이면 가장 큰 크기(harvest_emptyruns.py: 11건 중 10건, 첫 run 은 7건)
            let font_size = para
                .char_shapes
                .iter()
                .filter_map(|c| styles.char_styles.get(c.char_shape_id as usize))
                .map(|style| style.font_size)
                .fold(font_size, f64::max);
