// ==== find ====
        let style = styles.para_styles.get(para.para_shape_id as usize);
        let margin_left = style.map(|s| s.margin_left).unwrap_or(0.0);
        let margin_right = style.map(|s| s.margin_right).unwrap_or(0.0);
        (inner_px - margin_left - margin_right).max(0.0)
// ==== replace ====
        let style = styles.para_styles.get(para.para_shape_id as usize);
        // [claude-hwpx narrow-margin-ignore] 남는 폭이 25% 미만이면 여백을 무시한다
        if style.is_some_and(|s| crate::renderer::style_resolver::claude_margins_ignored(s, inner_px)) {
            return inner_px;
        }
        let margin_left = style.map(|s| s.margin_left).unwrap_or(0.0);
        let margin_right = style.map(|s| s.margin_right).unwrap_or(0.0);
        (inner_px - margin_left - margin_right).max(0.0)
