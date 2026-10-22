// ==== find ====
pub(crate) fn is_line_end_forbidden(ch: char) -> bool {
// ==== replace ====
/// [claude-hwpx dot-latin-glue] `idx` 앞 글자가 가운뎃점이고 `idx` 가 ASCII 영문자나 숫자면 그 사이는 꺾지 않는다.
/// 한/글 새 정답본 327문서에서 가운뎃점 뒤가 라틴인 307곳 모두 가운뎃점 앞뒤로 꺾지 않았다(「블|록·AI」).
fn claude_dot_latin_glue(text_chars: &[char], idx: usize) -> bool {
    idx > 0
        && idx < text_chars.len()
        && text_chars[idx].is_ascii_alphanumeric()
        && matches!(
            text_chars[idx - 1],
            '\u{00B7}' | '\u{30FB}' | '\u{FF65}' | '\u{2027}' | '\u{2219}'
        )
}

pub(crate) fn is_line_end_forbidden(ch: char) -> bool {
// ==== next ====
                    if allow_break {
                        cursor.last_break_token_idx = Some(ti);
                        cursor.last_break_char_idx = *end_idx; // 이 글자 다음 (이 글자 포함)
// ==== replace ====
                    if allow_break && !claude_dot_latin_glue(text_chars, *end_idx) {
                        cursor.last_break_token_idx = Some(ti);
                        cursor.last_break_char_idx = *end_idx; // 이 글자 다음 (이 글자 포함)
// ==== next ====
                    if allow_break {
                        last_break_token_idx = Some(ti);
                        last_break_char_idx = *end_idx; // 이 글자 다음 (이 글자 포함)
// ==== replace ====
                    if allow_break && !claude_dot_latin_glue(text_chars, *end_idx) {
                        last_break_token_idx = Some(ti);
                        last_break_char_idx = *end_idx; // 이 글자 다음 (이 글자 포함)
