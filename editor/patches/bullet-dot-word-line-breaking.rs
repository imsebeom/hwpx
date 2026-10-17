// ==== find ====
        && ('가'..='힣').contains(&text_chars[idx])
        && text_chars[idx - 1].is_ascii_alphanumeric()
}
// ==== replace ====
        && ('가'..='힣').contains(&text_chars[idx])
        // [claude-hwpx bullet-dot-word] 「•」 뒤 한글 앞도 꺾는 자리(lab e33)
        && (text_chars[idx - 1].is_ascii_alphanumeric() || text_chars[idx - 1] == '\u{2022}')
}
