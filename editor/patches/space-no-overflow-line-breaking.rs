// ==== find ====
fn recalc_width_hwp(tokens: &[BreakToken], current_token_idx: usize, new_line_start: usize) -> i32 {
// ==== replace ====
/// [claude-hwpx space-no-overflow] 줄을 `break_idx` 에서 꺾을 때, 그 자리의 빈칸 묶음 가운데 줄 폭 안에 드는 빈칸까지만 앞줄에 두고
/// 나머지 빈칸부터 다음 줄을 시작할 자리. 한/글은 시작 위치가 줄 폭을 넘는 빈칸을 다음 줄로 보낸다(e19, 정답본 101곳).
/// 묶음이 통째로 들어가거나 빈칸이 없거나 줄에 탭이 있으면 None(종전대로 빈칸을 앞줄에 매단다).
fn claude_space_run_split(
    tokens: &[BreakToken],
    text_chars: &[char],
    line_start: usize,
    break_idx: usize,
    effective_width: i32,
) -> Option<usize> {
    let mut run_start = break_idx.min(text_chars.len());
    while run_start > line_start && text_chars[run_start - 1] == ' ' {
        run_start -= 1;
    }
    let mut run_end = break_idx;
    while run_end < text_chars.len() && text_chars[run_end] == ' ' {
        run_end += 1;
    }
    if run_start >= run_end || run_start <= line_start {
        return None;
    }
    let mut before = 0i32;
    let mut spaces: Vec<(usize, i32)> = Vec::new();
    for t in tokens {
        match t {
            BreakToken::Text { start_idx, end_idx, base_width, .. } => {
                if *start_idx >= line_start && *end_idx <= run_start {
                    before += to_hwp(*base_width);
                } else if *start_idx < run_start && *end_idx > line_start {
                    return None; // 묶음 경계에 걸친 토큰(줄 시작 앞에서 시작한 것 등)
                }
            }
            BreakToken::Space { idx, width, .. } => {
                if *idx >= line_start && *idx < run_start {
                    before += to_hwp(*width);
                } else if *idx >= run_start && *idx < run_end {
                    spaces.push((*idx, to_hwp(*width)));
                }
            }
            BreakToken::Tab { idx, .. } if *idx >= line_start && *idx < run_end => return None,
            _ => {}
        }
    }
    // 글자만으로 줄 폭을 넘어 빈칸 압축(condense)으로 들어온 줄은 끝 빈칸을 모두 앞줄에 둔다(d048)
    if spaces.len() != run_end - run_start || before > effective_width {
        return None;
    }
    // 빈칸은 시작 위치가 줄 폭 이하이면 앞줄에 남는다(자기 폭만큼은 넘친다). e19: 남은 폭 8.1pt 에 5pt 빈칸 2개
    let mut w = before;
    for (idx, sw) in spaces {
        if w > effective_width {
            return Some(idx);
        }
        w += sw;
    }
    None
}

fn recalc_width_hwp(tokens: &[BreakToken], current_token_idx: usize, new_line_start: usize) -> i32 {
// ==== next ====
                        if let Some(break_token_idx) = cursor.last_break_token_idx {
                            let result = LineBreakResult {
                                start_idx: cursor.line_start_idx,
                                end_idx: cursor.last_break_char_idx,
                                max_font_size: cursor.fs_at_last_break,
                                has_line_break: false,
                            };
                            let mut next_start = cursor.last_break_char_idx;
                            while next_start < text_chars.len() && text_chars[next_start] == ' ' {
                                next_start += 1;
                            }
// ==== replace ====
                        if let Some(break_token_idx) = cursor.last_break_token_idx {
                            let mut result = LineBreakResult {
                                start_idx: cursor.line_start_idx,
                                end_idx: cursor.last_break_char_idx,
                                max_font_size: cursor.fs_at_last_break,
                                has_line_break: false,
                            };
                            let mut next_start = cursor.last_break_char_idx;
                            while next_start < text_chars.len() && text_chars[next_start] == ' ' {
                                next_start += 1;
                            }
                            // [claude-hwpx space-no-overflow] 줄 폭을 넘는 빈칸부터 다음 줄로
                            if let Some(split) = claude_space_run_split(
                                tokens,
                                text_chars,
                                cursor.line_start_idx,
                                cursor.last_break_char_idx,
                                eff_w(cursor.is_first_line),
                            ) {
                                result.end_idx = split;
                                next_start = split;
                            }
// ==== next ====
                        if let Some(break_token_idx) = last_break_token_idx {
                            results.push(LineBreakResult {
                                start_idx: line_start_idx,
                                end_idx: last_break_char_idx,
                                max_font_size: fs_at_last_break,
                                has_line_break: false,
                            });
                            let mut next_start = last_break_char_idx;
                            while next_start < text_chars.len() && text_chars[next_start] == ' ' {
                                next_start += 1;
                            }
// ==== replace ====
                        if let Some(break_token_idx) = last_break_token_idx {
                            // [claude-hwpx space-no-overflow] 운영 경로와 같게(동등성 시험용 사본)
                            let split = claude_space_run_split(
                                tokens,
                                text_chars,
                                line_start_idx,
                                last_break_char_idx,
                                eff_w(is_first_line),
                            );
                            results.push(LineBreakResult {
                                start_idx: line_start_idx,
                                end_idx: split.unwrap_or(last_break_char_idx),
                                max_font_size: fs_at_last_break,
                                has_line_break: false,
                            });
                            let mut next_start = last_break_char_idx;
                            while next_start < text_chars.len() && text_chars[next_start] == ' ' {
                                next_start += 1;
                            }
                            if let Some(split) = split {
                                next_start = split;
                            }
