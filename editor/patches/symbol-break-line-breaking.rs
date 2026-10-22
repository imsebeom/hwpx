// ==== find ====
                    } else {
                        is_cjk_ideograph(c)
                    };
// ==== replace ====
                    } else {
                        // [claude-hwpx symbol-break] 글자 단위에서 기호도 뒤를 꺾는 자리로
                        is_cjk_ideograph(c) || (korean_break_unit == 1 && claude_symbol_break(c))
                    };
// ==== next ====
/// [claude-hwpx latin-hangul-break] `idx` 의 한글 앞이 ASCII 영문자나 숫자라 그 사이에서 줄을 꺾을 수 있는지(「AI를」, 「10문항」).
// ==== replace ====
/// [claude-hwpx symbol-break] 글자 단위에서 한자처럼 앞뒤를 꺾는 기호(사본 실험 sb: ㎡, →, ※, ①, ○). 줄 머리 금칙(℃ 등)과 줄 끝 금칙은 뺀다.
fn claude_symbol_break(ch: char) -> bool {
    (matches!(ch as u32, 0x3380..=0x33FF | 0x2190..=0x21FF | 0x2460..=0x24FF | 0x25A0..=0x25FF) || ch == '\u{203B}')
        && !is_line_start_forbidden(ch)
        && !is_line_end_forbidden(ch)
}

/// [claude-hwpx latin-hangul-break] `idx` 의 한글 앞이 ASCII 영문자나 숫자라 그 사이에서 줄을 꺾을 수 있는지(「AI를」, 「10문항」).
// ==== next ====
fn claude_latin_hangul_boundary(text_chars: &[char], idx: usize) -> bool {
    idx > 0
// ==== replace ====
fn claude_latin_hangul_boundary(text_chars: &[char], idx: usize) -> bool {
    // [claude-hwpx symbol-break] 라틴, 숫자 뒤 기호 앞도(「101.25|㎡」)
    if idx > 0
        && idx < text_chars.len()
        && claude_symbol_break(text_chars[idx])
        && text_chars[idx - 1].is_ascii_alphanumeric()
    {
        return true;
    }
    idx > 0
// ==== next ====
            || ('\u{2160}'..='\u{2188}').contains(&text_chars[idx - 1]))
// ==== replace ====
            || ('\u{2160}'..='\u{2188}').contains(&text_chars[idx - 1])
            // [claude-hwpx symbol-break] 「%」, 「℃」 뒤 한글 앞도(「12345678%|가나」)
            || matches!(text_chars[idx - 1], '%' | '\u{2103}'))
