// ==== find ====
pub(crate) fn is_line_end_forbidden(ch: char) -> bool {
// ==== replace ====
/// [claude-hwpx char-kinsoku] 글자 단위 줄 나눔의 한 덩이: 글자 하나, 또는 한글 한 글자와 바로 뒤의 줄 머리 금칙 문자.
///
/// 한/글은 글자 단위로 나눌 때도 마침표, 쉼표, 닫는 괄호가 줄 처음에 오지 않게 앞 글자를 함께 다음 줄로 내린다
/// (2026-10-05 한/글 재저장 317개 문서: 금칙 문자가 줄 머리에 걸린 94건 모두 정확히 한 글자 앞에서 꺾음).
/// 종전에는 어절 단위에서만 금칙 문자를 붙여, 글자 단위 문단은 「다」 뒤에서 꺾고 「.」만 다음 줄에 두었다.
fn claude_is_glyph_unit(text_chars: &[char], start: usize, end: usize) -> bool {
    end == start + 1
        || (end > start + 1
            && end <= text_chars.len()
            && is_hangul(text_chars[start])
            && text_chars[start + 1..end]
                .iter()
                .all(|c| is_line_start_forbidden(*c)))
}

pub(crate) fn is_line_end_forbidden(ch: char) -> bool {
// ==== next ====
                let w = estimate_text_width_unrounded(&ch.to_string(), &ts)
                    + inline_width_px_at(inline_controls, i);
                tokens.push(BreakToken::Text {
                    start_idx: i,
                    end_idx: i + 1,
                    base_width: w,
                    width: w,
                    max_font_size: fs,
                    base_char_widths: vec![],
                    char_widths: vec![],
                });
                i += 1;
                continue;
            }
        }

        // 라틴 단어 또는 글자
// ==== replace ====
                let mut w = estimate_text_width_unrounded(&ch.to_string(), &ts)
                    + inline_width_px_at(inline_controls, i);
                // 뒤따르는 줄 머리 금칙 문자를 이 글자와 한 덩이로 묶는다(claude_is_glyph_unit)
                let start = i;
                let mut unit_widths = vec![w];
                i += 1;
                while i < text_len && is_line_start_forbidden(text_chars[i]) {
                    let forbidden_width = measure_char_width(
                        text_chars[i],
                        i,
                        char_offsets,
                        char_shapes,
                        styles,
                        current_lang,
                        inline_controls,
                    );
                    unit_widths.push(forbidden_width);
                    w += forbidden_width;
                    i += 1;
                }
                let unit_widths = if unit_widths.len() > 1 {
                    unit_widths
                } else {
                    Vec::new()
                };
                tokens.push(BreakToken::Text {
                    start_idx: start,
                    end_idx: i,
                    base_width: w,
                    width: w,
                    max_font_size: fs,
                    base_char_widths: unit_widths.clone(),
                    char_widths: unit_widths,
                });
                continue;
            }
        }

        // 라틴 단어 또는 글자
// ==== next ====
                if *end_idx - *start_idx == 1 && *start_idx > cursor.line_start_idx && token_fits {
// ==== replace ====
                if claude_is_glyph_unit(text_chars, *start_idx, *end_idx)
                    && *start_idx > cursor.line_start_idx
                    && token_fits
                {
// ==== next ====
                if *end_idx - *start_idx == 1 && *start_idx > line_start_idx && token_fits {
// ==== replace ====
                if claude_is_glyph_unit(text_chars, *start_idx, *end_idx)
                    && *start_idx > line_start_idx
                    && token_fits
                {
