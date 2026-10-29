// ==== find ====
                let combined: f64 = (r..r + span).map(|i| row_heights[i]).sum();
// ==== replace ====
                // [claude-hwpx span-ladder-trust] HWPX 글자처럼 취급 표의 걸친 칸: 뒤 줄이 그림 아래에서 시작하면 저장 줄이 그림 자리를 담았다 — 그림을 또 더하지 않는다
                // (결과보고서 160번 표 10행: 한/글 58.3px = 줄 끝 4084 + 여백, 엔진 65.7px)
                let required_height = if !self.is_native_hwp5
                    && !self.is_hwp3_variant
                    && table.common.treat_as_char
                    && non_inline_h > 0.0
                    && cell.text_direction == 0
                    && cell.paragraphs.iter().all(|p| {
                        !p.line_segs.is_empty() && p.line_segs.iter().all(|s| s.tag & 0x8000_0000 == 0)
                    })
                    && cell.paragraphs.iter().enumerate().any(|(i, pp)| {
                        let obj_h = pp
                            .controls
                            .iter()
                            .filter_map(|c| match c {
                                Control::Picture(pic) if !pic.common.treat_as_char => {
                                    Some(self.non_inline_control_flow_height(&pic.common))
                                }
                                Control::Shape(sh) if !sh.common().treat_as_char => {
                                    Some(self.non_inline_control_flow_height(sh.common()))
                                }
                                _ => None,
                            })
                            .fold(0.0f64, f64::max);
                        let own_top = pp
                            .line_segs
                            .first()
                            .map(|s| hwpunit_to_px(s.vertical_pos, self.dpi))
                            .unwrap_or(0.0);
                        obj_h > 0.0
                            && cell.paragraphs[i + 1..]
                                .iter()
                                .find_map(|later| later.line_segs.first())
                                .is_some_and(|s| hwpunit_to_px(s.vertical_pos, self.dpi) + 0.5 >= own_top + obj_h)
                    }) {
                    let (mut next_top, mut end) = (0i64, 0i64);
                    for s in cell.paragraphs.iter().flat_map(|p| p.line_segs.iter()) {
                        let top = i64::from(s.vertical_pos).max(next_top);
                        end = end.max(top + i64::from(s.line_height));
                        next_top = top + i64::from(s.line_height) + i64::from(s.line_spacing.max(0));
                    }
                    hwpunit_to_px(end as i32, self.dpi).max(nested_bottom).max(wrap_bottom) + pad_top + pad_bottom
                } else {
                    required_height
                };
                let combined: f64 = (r..r + span).map(|i| row_heights[i]).sum();
// ==== next ====
            for &(r, span, total_h) in &constraints {
                let known_sum: f64 = (r..r + span).map(|i| row_heights[i]).sum();
                if total_h > known_sum + 0.5 {
                    row_heights[r + span - 1] += total_h - known_sum;
                }
            }
// ==== replace ====
            // [claude-hwpx span-ladder-trust] HWPX 글자처럼 취급 표는 이 보충을 2-c(칸 내용) 뒤로 미룬다 — 먼저 더하면 2-c 가 다른 행을
            // 키운 뒤에도 남아 묶음이 커진다(결과보고서 160번 표 10행: 엔진 43.4, 한/글 35.9 = c13 선언 9961 - 8행 - 9행)
            let claude_defer_declared_span = !self.is_native_hwp5 && !self.is_hwp3_variant && table.common.treat_as_char;
            for &(r, span, total_h) in &constraints {
                if claude_defer_declared_span {
                    break;
                }
                let known_sum: f64 = (r..r + span).map(|i| row_heights[i]).sum();
                if total_h > known_sum + 0.5 {
                    row_heights[r + span - 1] += total_h - known_sum;
                }
            }
// ==== next ====
        // 3단계: 높이가 0인 행은 기본값 적용
// ==== replace ====
        // [claude-hwpx span-ladder-trust] 미뤄 둔 병합 칸 선언 보충(#2291): 칸 내용으로 키운 뒤에도 선언보다 모자라면 마지막 걸침 행에
        if !self.is_native_hwp5 && !self.is_hwp3_variant && table.common.treat_as_char {
            for cell in &table.cells {
                let r = cell.row as usize;
                let span = cell.row_span as usize;
                if span > 1 && r + span <= row_count && cell.height < 0x8000_0000 {
                    let total_h = hwpunit_to_px(cell.height as i32, self.dpi);
                    let known_sum: f64 = (r..r + span).map(|i| row_heights[i]).sum();
                    if total_h > known_sum + 0.5 {
                        row_heights[r + span - 1] += total_h - known_sum;
                    }
                }
            }
        }
        // 3단계: 높이가 0인 행은 기본값 적용
