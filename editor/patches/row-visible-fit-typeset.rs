// ==== find ====
            if !splittable {
                // [#2236 진단] 분할 불가 정지 — 동작 불변.
// ==== replace ====
            // [claude-hwpx row-visible-fit] 분할 불가 행도 위 여백 + 줄들(마지막 줄 간격 빼고) + 아래 여백이 남은 자리에 들어가면 이 쪽에 남은 높이로 둔다
            // (쪽번호시험 사본 실험: 32px 행이 남은 17.42px 에서 담기고 17.1px 에서 넘어간다 = 142 + 1000 + 142. d194 도 같은 규칙)
            if !splittable
                && st.profile.hwpx_container()
                && mt.allows_row_break_split()
                && r > cursor_row
                && row_start_cut.is_empty()
                && !rowspan_touched[r]
            {
                let rest = (avail_for_rows - consumed - cs_before).max(0.0);
                let visible = table
                    .cells
                    .iter()
                    .filter(|cell| cell.row as usize == r && cell.row_span == 1)
                    .map(|cell| {
                        if cell.paragraphs.iter().any(|p| !p.controls.is_empty() || p.line_segs.is_empty()) {
                            return f64::INFINITY;
                        }
                        let pad = cell.effective_padding_in(table);
                        let lines: i32 = cell
                            .paragraphs
                            .iter()
                            .flat_map(|p| p.line_segs.iter())
                            .map(|s| s.line_height + s.line_spacing.max(0))
                            .sum();
                        let last_ls = cell
                            .paragraphs
                            .last()
                            .and_then(|p| p.line_segs.last())
                            .map(|s| s.line_spacing.max(0))
                            .unwrap_or(0);
                        hwpunit_to_px(pad.top as i32 + lines - last_ls + pad.bottom as i32, self.dpi)
                    })
                    .fold(0.0f64, f64::max);
                if visible > 0.0 && visible.is_finite() && visible <= rest + 0.01 {
                    consumed += cs_before + rest;
                    r += 1;
                    end_row = r;
                    end_row_height_override = Some(rest);
                    continue;
                }
            }
            if !splittable {
                // [#2236 진단] 분할 불가 정지 — 동작 불변.
