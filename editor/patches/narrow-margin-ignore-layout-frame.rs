// ==== find ====
        let margin_left = style.map(|s| s.margin_left).unwrap_or(0.0);
        let margin_right = style.map(|s| s.margin_right).unwrap_or(0.0);
        let head_type = style.map(|s| s.head_type).unwrap_or(HeadType::None);
// ==== replace ====
        // [claude-hwpx narrow-margin-ignore] 남는 폭이 25% 미만이면 여백을 무시한다
        let claude_ignored = style
            .is_some_and(|s| crate::renderer::style_resolver::claude_margins_ignored(s, column_width_px));
        let margin_left = if claude_ignored { 0.0 } else { style.map(|s| s.margin_left).unwrap_or(0.0) };
        let margin_right = if claude_ignored { 0.0 } else { style.map(|s| s.margin_right).unwrap_or(0.0) };
        let head_type = style.map(|s| s.head_type).unwrap_or(HeadType::None);
