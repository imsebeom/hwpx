// ==== find ====
                    if !is_latin(c) && !is_lang_neutral(c) {
                        break;
                    }
                    // 하이픈 모드: 하이픈에서 분할 (하이픈 포함 후 분리)
// ==== replace ====
                    if !is_latin(c) && !is_lang_neutral(c) {
                        break;
                    }
                    // [claude-hwpx paren-dot-break] 글자 단위에서 괄호 안이 한글이면 「(」 앞에서 토큰을 끊는다(그 앞이 꺾을 자리)
                    if korean_break_unit == 1
                        && c == '('
                        && !token_text.is_empty()
                        && i + 1 < text_len
                        && ('가'..='힣').contains(&text_chars[i + 1])
                    {
                        break;
                    }
                    // 하이픈 모드: 하이픈에서 분할 (하이픈 포함 후 분리)
// ==== next ====
                        cursor.fs_at_last_break = cursor.line_max_fs;
                    }
                }
                if !token_fits {
// ==== replace ====
                        cursor.fs_at_last_break = cursor.line_max_fs;
                    }
                }
                // [claude-hwpx paren-dot-break] 라틴, 숫자 뒤 「(」(괄호 안이 한글)는 「(」 까지 줄에 들 때만 그 앞을 꺾을 자리로(실험 pc)
                if korean_break_unit == 1
                    && token_fits
                    && ti > 0
                    && *start_idx > cursor.line_start_idx
                    && claude_latin_paren_boundary(text_chars, *start_idx)
                {
                    cursor.last_break_token_idx = Some(ti - 1);
                    cursor.last_break_char_idx = *start_idx;
                    cursor.width_at_last_break = cursor.lw;
                    cursor.space_savings_at_last_break = cursor.line_space_savings;
                    cursor.fs_at_last_break = cursor.line_max_fs;
                }
                if !token_fits {
// ==== next ====
                        fs_at_last_break = line_max_fs;
                    }
                }
                if !text_token_fits_line_hwp(
// ==== replace ====
                        fs_at_last_break = line_max_fs;
                    }
                }
                // [claude-hwpx paren-dot-break] 라틴, 숫자 뒤 「(」(괄호 안이 한글)는 「(」 까지 줄에 들 때만 그 앞을 꺾을 자리로(실험 pc)
                if korean_break_unit == 1
                    && token_fits
                    && ti > 0
                    && *start_idx > line_start_idx
                    && claude_latin_paren_boundary(text_chars, *start_idx)
                {
                    last_break_token_idx = Some(ti - 1);
                    last_break_char_idx = *start_idx;
                    width_at_last_break = lw;
                    space_savings_at_last_break = line_space_savings;
                    fs_at_last_break = line_max_fs;
                }
                if !text_token_fits_line_hwp(
// ==== next ====
/// [claude-hwpx latin-hangul-break] `idx` 의 한글 앞이 ASCII 영문자나 숫자라 그 사이에서 줄을 꺾을 수 있는지(「AI를」, 「10문항」).
// ==== replace ====
/// [claude-hwpx paren-dot-break] `idx` 가 「(」 이고 그 앞이 ASCII 영문자나 숫자, 뒤가 한글인지(「chamber|(이중」, 「7/25|(화)」)
fn claude_latin_paren_boundary(text_chars: &[char], idx: usize) -> bool {
    idx > 0
        && idx + 1 < text_chars.len()
        && text_chars[idx] == '('
        && ('가'..='힣').contains(&text_chars[idx + 1])
        && text_chars[idx - 1].is_ascii_alphanumeric()
}

/// [claude-hwpx latin-hangul-break] `idx` 의 한글 앞이 ASCII 영문자나 숫자라 그 사이에서 줄을 꺾을 수 있는지(「AI를」, 「10문항」).
// ==== next ====
                ']' | ')' | '}' | '\'' | '/' | ',' | '-' | '\u{300D}' | '\u{300F}' | '\u{2019}' | '\u{201D}'
            ))
// ==== replace ====
                ']' | ')' | '}' | '\'' | '/' | ',' | '-' | '\u{300D}' | '\u{300F}' | '\u{2019}' | '\u{201D}'
            )
            // [claude-hwpx paren-dot-break] 가운뎃점 뒤(「AI·|컴퓨터」), 로마 숫자 뒤(「(Ⅲ|단계」) 한글 앞도
            || matches!(text_chars[idx - 1], '\u{00B7}' | '\u{30FB}' | '\u{FF65}' | '\u{2027}' | '\u{2219}')
            || ('\u{2160}'..='\u{2188}').contains(&text_chars[idx - 1]))
