// ==== find ====
                        .iter()
                        .collect();
                    let inner_text = decode_html_entities(&html_strip_tags(&inner));

                    if !inner_text.is_empty() {
// ==== replace ====
                        .iter()
                        .collect();
                    // [claude-hwpx html-paste-whitespace] span 안 글의 소스 줄바꿈도 접는다
                    let inner_text =
                        decode_html_entities(&claude_collapse_html_whitespace(&html_strip_tags(&inner)));

                    if !inner_text.is_empty() {
// ==== next ====
                let raw: String = chars[text_start..pos].iter().collect();
                let decoded = decode_html_entities(&raw);
// ==== replace ====
                let raw: String = chars[text_start..pos].iter().collect();
                // [claude-hwpx html-paste-whitespace] HTML 소스의 줄바꿈은 글이 아니다. 태그 사이 들여쓰기(줄바꿈만 있는 공백)는 버리고,
                // 글 속 줄바꿈과 탭은 공백 하나로 접는다(브라우저 렌더 규칙). 종전에는 rhwp 가 내보낸 칸 HTML
                // (`<p ...>\n<span>문화</span></p>`)을 붙이면 문단 첫머리에 줄바꿈 문자가 들어갔다(2026-10-06 칸 블록 붙이기)
                if raw.contains(['\n', '\r']) && raw.trim().is_empty() {
                    continue;
                }
                let raw = claude_collapse_html_whitespace(&raw);
                let decoded = decode_html_entities(&raw);
// ==== next ====
}

#[cfg(test)]
mod tests {
// ==== replace ====
}

/// [claude-hwpx html-paste-whitespace] HTML 글 조각의 줄바꿈, 탭, 그 둘레 공백을 공백 하나로 접는다(일반 공백 연속은 그대로 둔다).
fn claude_collapse_html_whitespace(raw: &str) -> String {
    if !raw.contains(['\n', '\r', '\t']) {
        return raw.to_string();
    }
    let mut out = String::with_capacity(raw.len());
    let mut chars = raw.chars().peekable();
    while let Some(ch) = chars.next() {
        if matches!(ch, '\n' | '\r' | '\t') {
            while out.ends_with(' ') {
                out.pop();
            }
            while matches!(chars.peek(), Some(' ' | '\n' | '\r' | '\t')) {
                chars.next();
            }
            out.push(' ');
        } else {
            out.push(ch);
        }
    }
    out
}

#[cfg(test)]
mod tests {
