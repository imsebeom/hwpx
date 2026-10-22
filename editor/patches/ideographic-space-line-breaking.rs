// ==== find ====
        // 공백 (줄 바꿈 지점) — NonBreakingSpace(\u{00A0})는 제외
        if ch == ' ' {
// ==== replace ====
        // [claude-hwpx ideographic-space] 전각 빈칸은 빈칸처럼 꺾고 줄 끝에 매단다. 폭은 그 글꼴의 전각 빈칸 폭
        if ch == '\u{3000}' {
            let utf16_pos = if i < char_offsets.len() {
                char_offsets[i]
            } else {
                i as u32
            };
            let style_id = find_active_char_shape(char_shapes, utf16_pos);
            let ts = resolved_to_text_style(styles, style_id, current_lang);
            let font_size = if ts.font_size > 0.0 { ts.font_size } else { 12.0 };
            let w = estimate_text_width_unrounded("\u{3000}", &ts) + inline_width_px_at(inline_controls, i);
            tokens.push(BreakToken::Space {
                idx: i,
                width: w,
                max_font_size: font_size,
            });
            i += 1;
            continue;
        }

        // 공백 (줄 바꿈 지점) — NonBreakingSpace(\u{00A0})는 제외
        if ch == ' ' {
// ==== next ====
                            let mut next_start = cursor.last_break_char_idx;
                            while next_start < text_chars.len() && text_chars[next_start] == ' ' {
// ==== replace ====
                            let mut next_start = cursor.last_break_char_idx;
                            while next_start < text_chars.len() && matches!(text_chars[next_start], ' ' | '\u{3000}') {
// ==== next ====
                            let mut next_start = last_break_char_idx;
                            while next_start < text_chars.len() && text_chars[next_start] == ' ' {
// ==== replace ====
                            let mut next_start = last_break_char_idx;
                            while next_start < text_chars.len() && matches!(text_chars[next_start], ' ' | '\u{3000}') {
