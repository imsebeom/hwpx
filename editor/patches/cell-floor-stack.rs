// ==== find ====
                let content_hu = cell
                    .paragraphs
                    .iter()
                    .flat_map(|p| p.line_segs.iter())
                    .map(|seg| i64::from(seg.vertical_pos) + i64::from(seg.line_height))
                    .max()
                    .unwrap_or(0);
// ==== replace ====
                // [claude-hwpx cell-floor-stack] 비례 축소의 행별 하한도 줄을 차례로 쌓아 잰다(tac-row-ladder 와 같은 셈).
                // 낡은 vertpos(그림을 바꿔 넣은 칸의 뒤 빈 문단 1600)를 그대로 믿으면 하한이 낮아져 그 줄을 눌렀다(2026-10-02)
                let content_hu = {
                    let (mut next_top, mut end) = (0i64, 0i64);
                    for seg in cell.paragraphs.iter().flat_map(|p| p.line_segs.iter()) {
                        let top = i64::from(seg.vertical_pos).max(next_top);
                        end = end.max(top + i64::from(seg.line_height));
                        next_top = top + i64::from(seg.line_height) + i64::from(seg.line_spacing.max(0));
                    }
                    end
                };
