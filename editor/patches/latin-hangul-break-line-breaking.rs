// ==== find ====
fn recalc_width_hwp(tokens: &[BreakToken], current_token_idx: usize, new_line_start: usize) -> i32 {
// ==== replace ====
/// [claude-hwpx latin-hangul-break] `idx` 의 한글 앞이 ASCII 영문자나 숫자라 그 사이에서 줄을 꺾을 수 있는지(「AI를」, 「10문항」).
fn claude_latin_hangul_boundary(text_chars: &[char], idx: usize) -> bool {
    idx > 0
        && idx < text_chars.len()
        && ('가'..='힣').contains(&text_chars[idx])
        && text_chars[idx - 1].is_ascii_alphanumeric()
}

fn recalc_width_hwp(tokens: &[BreakToken], current_token_idx: usize, new_line_start: usize) -> i32 {
// ==== next ====
                claude_note_token_start(text_chars, *start_idx);
                if let Some(next_char_idx) = cursor.fallback_char_idx {
// ==== replace ====
                claude_note_token_start(text_chars, *start_idx);
                // [claude-hwpx latin-hangul-break] 라틴, 숫자 바로 뒤 한글의 앞도 꺾을 자리다
                if cursor.fallback_char_idx.is_none()
                    && korean_break_unit == 1
                    && ti > 0
                    && *start_idx > cursor.line_start_idx
                    && claude_latin_hangul_boundary(text_chars, *start_idx)
                {
                    cursor.last_break_token_idx = Some(ti - 1);
                    cursor.last_break_char_idx = *start_idx;
                    cursor.width_at_last_break = cursor.lw;
                    cursor.space_savings_at_last_break = cursor.line_space_savings;
                    cursor.fs_at_last_break = cursor.line_max_fs;
                }
                if let Some(next_char_idx) = cursor.fallback_char_idx {
// ==== next ====
                claude_note_token_start(text_chars, *start_idx);
                if *max_font_size > line_max_fs {
// ==== replace ====
                claude_note_token_start(text_chars, *start_idx);
                // [claude-hwpx latin-hangul-break] 운영 경로와 같게(동등성 시험용 사본)
                if korean_break_unit == 1
                    && ti > 0
                    && *start_idx > line_start_idx
                    && claude_latin_hangul_boundary(text_chars, *start_idx)
                {
                    last_break_token_idx = Some(ti - 1);
                    last_break_char_idx = *start_idx;
                    width_at_last_break = lw;
                    space_savings_at_last_break = line_space_savings;
                    fs_at_last_break = line_max_fs;
                }
                if *max_font_size > line_max_fs {
