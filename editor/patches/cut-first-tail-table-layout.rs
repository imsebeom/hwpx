// ==== find ====
                if j > start && h + u.height > avail_height + ROW_CUT_CAPACITY_FP_EPSILON_PX {
                    if std::env::var("RHWP_DIAG_6368").is_ok() {
                        let over = h + u.height - avail_height;
                        if over <= 2.0 {
                            eprintln!(
                                "DIAG_6368 cap-cut
// ==== replace ====
                // [claude-hwpx cut-first-tail] 조각의 첫 줄도 뒤 줄 간격만 넘치면 담고 멈춘다(d042 1쪽 행 2 첫 줄)
                if j == start
                    && self.profile.get().hwpx_container()
                    && h + u.height > avail_height + ROW_CUT_CAPACITY_FP_EPSILON_PX
                    && !u.empty_spacer
                    && u.nested_row.is_none()
                    && u.nested_table_fragment.is_none()
                    && u.vis_end == u.vis_start + 1
                    && j + 1 < units.len()
                    // 여러 행에 걸친 칸이 이 행에서 시작하면 한/글은 넘긴다(d139 행 7: ⓓ 칸 rowSpan 3 시작, 예산 16.2).
                    // 앞 행에서 시작해 이 행에 걸친 칸은 상관없다(d200 행 16 은 담는다)
                    && !table
                        .cells
                        .iter()
                        .any(|c| c.row_span > 1 && c.row as usize == row)
                {
                    let claude_tail = cell
                        .paragraphs
                        .get(u.para_idx)
                        .and_then(|p| p.line_segs.get(u.vis_start))
                        .map(|s| hwpunit_to_px(s.line_spacing.max(0), self.dpi))
                        .unwrap_or(0.0)
                        .min(u.height);
                    if claude_tail > 0.0
                        && h + u.height - claude_tail <= avail_height + ROW_CUT_CAPACITY_FP_EPSILON_PX
                    {
                        h += u.height - claude_tail;
                        j += 1;
                        break;
                    }
                }
                if j > start && h + u.height > avail_height + ROW_CUT_CAPACITY_FP_EPSILON_PX {
                    if std::env::var("RHWP_DIAG_6368").is_ok() {
                        let over = h + u.height - avail_height;
                        if over <= 2.0 {
                            eprintln!(
                                "DIAG_6368 cap-cut
