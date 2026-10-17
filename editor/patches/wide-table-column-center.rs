// ==== find ====
                HorzAlign::Center => ref_x + (ref_w - table_width).max(0.0) / 2.0 + h_offset,
// ==== replace ====
                // [claude-hwpx wide-table-column-center] 단보다 넓은 「단 기준 가운데」 표는 한/글이 단 가운데에 두고 양쪽으로
                // 넘긴다(2026-10-17 교과 평가계획: 단 642.5px, 표 681.5px — 한/글 PDF 6개 표 모두 왼쪽 56.1 = 75.6 - 19.5).
                // 종전에는 넘침을 0 으로 잘라 단 왼쪽에 붙였다(76px). 쪽, 문단 기준은 근거가 없어 그대로
                HorzAlign::Center if matches!(horz_rel_to, HorzRelTo::Column) => {
                    ref_x + (ref_w - table_width) / 2.0 + h_offset
                }
                HorzAlign::Center => ref_x + (ref_w - table_width).max(0.0) / 2.0 + h_offset,
