// ==== find ====
        && (text_chars[idx - 1].is_ascii_alphanumeric() || text_chars[idx - 1] == '\u{2022}')
}
// ==== replace ====
        && (text_chars[idx - 1].is_ascii_alphanumeric()
            || text_chars[idx - 1] == '\u{2022}'
            // [claude-hwpx close-hangul-break] 닫는 부호, 빗금, 쉼표, 붙임표 뒤 한글 앞도(새 정답본 「2]|는」, 「3」|을」, 「AI,|기반」)
            || matches!(
                text_chars[idx - 1],
                ']' | ')' | '}' | '\'' | '/' | ',' | '-' | '\u{300D}' | '\u{300F}' | '\u{2019}' | '\u{201D}'
            ))
}
