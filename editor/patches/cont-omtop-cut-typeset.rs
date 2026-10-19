// ==== find ====
            let mut budget =
                (avail_for_rows - consumed - cs_before - padding - claude_outer_bottom).max(0.0);
// ==== replace ====
            // [claude-hwpx cont-omtop-cut] 이어지는 조각은 쪽 위에 바깥 위 여백을 두고 그린다(partial-omtop-hwpx) — 예산에서도 뺀다(d072 3쪽)
            let claude_outer_bottom = claude_outer_bottom
                + if claude_outer_bottom > 0.0
                    && is_continuation
                    // 저장 줄 칸은 그리기가 저장 vpos 대로 이어 그려 새 자르기 자리와 어긋난다(저장 줄 지표 5442 → 5766) — 엔진이 만든 줄만
                    && table.cells.iter().all(|c| {
                        c.paragraphs.iter().all(crate::renderer::para_has_no_stored_line_segs)
                    })
                {
                    hwpunit_to_px(table.outer_margin_top as i32, self.dpi)
                } else {
                    0.0
                };
            let mut budget =
                (avail_for_rows - consumed - cs_before - padding - claude_outer_bottom).max(0.0);
