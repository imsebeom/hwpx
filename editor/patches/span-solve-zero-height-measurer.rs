// ==== find ====
            constraints.sort_by_key(|&(_, span, _)| span);
            let max_iter = row_count + constraints.len();
            for _ in 0..max_iter {
                let mut progress = false;
                for &(r, span, total_h) in &constraints {
                    let known_sum: f64 = (r..r + span).map(|i| row_heights[i]).sum();
                    let unknown_rows: Vec<usize> =
                        (r..r + span).filter(|&i| row_heights[i] == 0.0).collect();
                    if unknown_rows.len() == 1 {
                        let remaining = (total_h - known_sum).max(0.0);
                        row_heights[unknown_rows[0]] = remaining;
                        progress = true;
                    }
                }
                if !progress {
                    break;
                }
            }
            for &(r, span, total_h) in &constraints {
                let known_sum: f64 = (r..r + span).map(|i| row_heights[i]).sum();
                let unknown_rows: Vec<usize> =
                    (r..r + span).filter(|&i| row_heights[i] == 0.0).collect();
// ==== replace ====
            constraints.sort_by_key(|&(_, span, _)| span);
            // [claude-hwpx span-solve-zero] HWPX 는 선언으로 0 이 된 행도 「아는 행」이다 — 0 을 모름으로 쓰면 그 행을 다시 풀어 남은 높이를 고르게 나눴다(d120 10~12행)
            let claude_hwpx = !self.is_native_hwp5 && !self.is_hwp3_variant;
            let mut claude_known: Vec<bool> = row_heights.iter().map(|h| *h != 0.0).collect();
            let max_iter = row_count + constraints.len();
            for _ in 0..max_iter {
                let mut progress = false;
                for &(r, span, total_h) in &constraints {
                    let known_sum: f64 = (r..r + span).map(|i| row_heights[i]).sum();
                    let unknown_rows: Vec<usize> = (r..r + span)
                        .filter(|&i| if claude_hwpx { !claude_known[i] } else { row_heights[i] == 0.0 })
                        .collect();
                    if unknown_rows.len() == 1 {
                        let remaining = total_h - known_sum;
                        // 음수로 풀리는(0 으로 깎이는) 행은 미룬다 — 다른 병합 칸이 양수로 정해 줄 수 있다(169번 표 16행: 한/글 277)
                        if claude_hwpx && remaining < 0.0 {
                            continue;
                        }
                        row_heights[unknown_rows[0]] = remaining.max(0.0);
                        claude_known[unknown_rows[0]] = true;
                        progress = true;
                    }
                }
                // 양수로 더 못 풀면 음수로 풀리는 행 하나를 0 으로 확정하고 다시 푼다(d120 10행)
                if !progress && claude_hwpx {
                    for &(r, span, _) in &constraints {
                        let unknown_rows: Vec<usize> = (r..r + span).filter(|&i| !claude_known[i]).collect();
                        if unknown_rows.len() == 1 {
                            row_heights[unknown_rows[0]] = 0.0;
                            claude_known[unknown_rows[0]] = true;
                            progress = true;
                            break;
                        }
                    }
                }
                if !progress {
                    break;
                }
            }
            for &(r, span, total_h) in &constraints {
                let known_sum: f64 = (r..r + span).map(|i| row_heights[i]).sum();
                let unknown_rows: Vec<usize> = (r..r + span)
                    .filter(|&i| if claude_hwpx { !claude_known[i] } else { row_heights[i] == 0.0 })
                    .collect();
// ==== next ====
    fn claude_empty_host_overlap(&self, paragraphs: &[Paragraph]) -> f64 {
        paragraphs
            .iter()
            .map(|para| {
// ==== replace ====
    fn claude_empty_host_overlap(&self, paragraphs: &[Paragraph]) -> f64 {
        // [claude-hwpx span-solve-zero] 칸 마지막 문단은 글 높이에서 줄 간격을 빼고 세므로(HWPX) 겹침도 줄 높이만 뺀다(d347 47번 표: 그림 칸이 줄 간격만큼 작았다)
        let claude_hwpx = !self.is_native_hwp5 && !self.is_hwp3_variant;
        let last = paragraphs.len().saturating_sub(1);
        paragraphs
            .iter()
            .enumerate()
            .map(|(claude_i, para)| {
                if claude_hwpx && claude_i == last {
                    let flow = para
                        .controls
                        .iter()
                        .map(|ctrl| match ctrl {
                            Control::Picture(pic) => self.non_inline_control_flow_height(&pic.common),
                            Control::Shape(shape) => self.non_inline_control_flow_height(shape.common()),
                            _ => 0.0,
                        })
                        .fold(0.0f64, f64::max);
                    let full = claude_empty_host_flow_overlap_px(para, flow, self.dpi);
                    let lh = para.line_segs.first().map(|s| hwpunit_to_px(s.line_height, self.dpi)).unwrap_or(0.0);
                    return full.min(lh);
                }
