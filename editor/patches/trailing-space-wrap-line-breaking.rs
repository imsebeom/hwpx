// ==== find ====
            BreakToken::Space {
                idx,
                width,
                max_font_size,
            } => {
                if *max_font_size > cursor.line_max_fs {
                    cursor.line_max_fs = *max_font_size;
                }
                cursor.last_break_token_idx = Some(ti);
// ==== replace ====
            BreakToken::Space {
                idx,
                width,
                max_font_size,
            } => {
                // [claude-hwpx trailing-space-wrap] 문단 끝 빈칸 묶음에서 시작 위치가 줄 폭을 넘는 빈칸부터 다음 줄로(d317 645, 661)
                if *idx > cursor.line_start_idx
                    && cursor.lw > eff_w(cursor.is_first_line)
                    // 글자처럼 놓인 개체의 폭이 얹힌 빈칸(글자 크기보다 넓음)은 빈칸으로 보지 않는다(d142 그림 묶음 문단)
                    && tokens[ti..].iter().all(|t| matches!(t, BreakToken::Space { width: w, max_font_size: f, .. } if *w <= *f))
                {
                    let mut run_w = 0i32;
                    let mut k = ti;
                    while k > 0 {
                        match &tokens[k - 1] {
                            BreakToken::Space { idx: si, width: sw, max_font_size: sf } if *si >= cursor.line_start_idx && *sw <= *sf => {
                                run_w += to_hwp(*sw);
                                k -= 1;
                            }
                            _ => break,
                        }
                    }
                    // 묶음의 처음 두 빈칸은 시작 위치와 상관없이 앞줄에 매단다(사본 실험 t2: 「가」43 + ii + 빈칸 2 는 한 줄)
                    if ti - k >= 2 && cursor.lw - run_w <= eff_w(cursor.is_first_line) {
                        let result = LineBreakResult {
                            start_idx: cursor.line_start_idx,
                            end_idx: *idx,
                            max_font_size: cursor.line_max_fs,
                            has_line_break: false,
                        };
                        cursor.line_start_idx = *idx;
                        cursor.lw = 0;
                        cursor.line_space_savings = 0;
                        cursor.line_max_fs = *max_font_size;
                        cursor.is_first_line = false;
                        cursor.last_break_token_idx = None;
                        cursor.emitted_any = true;
                        return Some(FilledInterval {
                            line: result,
                            termination: FillTermination::IntervalFull,
                        });
                    }
                }
                if *max_font_size > cursor.line_max_fs {
                    cursor.line_max_fs = *max_font_size;
                }
                cursor.last_break_token_idx = Some(ti);
