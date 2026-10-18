// ==== find ====
        let box_margin_left = para_style.map(|s| s.margin_left).unwrap_or(0.0);
        let box_margin_right = para_style.map(|s| s.margin_right).unwrap_or(0.0);
        let indent = para_style.map(|s| s.indent).unwrap_or(0.0);
// ==== replace ====
        // [claude-hwpx narrow-margin-ignore] 남는 폭이 25% 미만이면 여백과 들여쓰기를 모두 무시한다(줄 나눔과 같은 판정)
        let claude_ignored = para_style
            .is_some_and(|s| crate::renderer::style_resolver::claude_margins_ignored(s, col_area.width));
        let box_margin_left = if claude_ignored { 0.0 } else { para_style.map(|s| s.margin_left).unwrap_or(0.0) };
        let box_margin_right = if claude_ignored { 0.0 } else { para_style.map(|s| s.margin_right).unwrap_or(0.0) };
        let indent = if claude_ignored { 0.0 } else { para_style.map(|s| s.indent).unwrap_or(0.0) };
