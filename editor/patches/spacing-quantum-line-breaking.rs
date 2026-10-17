// ==== find ====
                let spacing = line_height_hwp as f64 * (ls_value - 100.0) / 100.0;
                if spacing > 0.0 {
                    (spacing / 4.0 + 0.5 + 1e-6).floor() as i32 * 4
// ==== replace ====
                let spacing = line_height_hwp as f64 * (ls_value - 100.0) / 100.0;
                if spacing > 0.0 {
                    // [claude-hwpx spacing-quantum] 줄 높이를 먼저 4 단위로 내린 뒤 비율을 곱해 반올림한다(정답본 105,341줄 중 96.60% 일치,
                    // 종전 식 95.93%). 동점에서 갈린다: 10.5pt 160% → 628, 9pt 130% → 272.
                    ((line_height_hwp / 4) as f64 * (ls_value - 100.0) / 100.0 + 0.5 + 1e-6).floor() as i32 * 4
