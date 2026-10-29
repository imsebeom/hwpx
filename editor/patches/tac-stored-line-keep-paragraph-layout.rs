// ==== find ====
                let table_wrapped = should_wrap_middle_anchored_table(
                    control_positions.get(*ctrl_idx).copied(),
                    text_chars.len(),
                    inline_x - line_start_x,
                    table_footprint,
                    right_margin - line_start_x,
                );
// ==== replace ====
                // [claude-hwpx tac-stored-line-keep] 저장 줄 배치가 있는 HWPX 문단은 저장 나눔이 권위다 — 표 위치 이하의 나눔이 남아 있을 때만 넘긴다
                // (결과보고서 189번: 글 + 빈칸 43개 + 표가 저장 한 줄인데 폭 어림으로 표를 다음 줄로 넘겨 본문이 43px 밀렸다)
                let claude_stored_lines = self.profile.get().hwpx_container()
                    && !para.line_segs.is_empty()
                    && para.line_segs.iter().all(|s| s.tag & 0x8000_0000 == 0);
                let table_wrapped = if claude_stored_lines {
                    let pos = control_positions.get(*ctrl_idx).copied().unwrap_or(0);
                    let wrap = next_break < line_break_char_indices.len()
                        && line_break_char_indices[next_break] <= pos
                        && inline_x > line_start_x + 1.0;
                    if wrap {
                        next_break += 1;
                    }
                    wrap
                } else {
                    should_wrap_middle_anchored_table(
                        control_positions.get(*ctrl_idx).copied(),
                        text_chars.len(),
                        inline_x - line_start_x,
                        table_footprint,
                        right_margin - line_start_x,
                    )
                };
