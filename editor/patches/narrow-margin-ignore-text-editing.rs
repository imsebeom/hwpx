// ==== find ====
        let para_style = styles.para_styles.get(para_shape_id as usize);
        let margin_left = para_style.map(|s| s.margin_left).unwrap_or(0.0);
        let margin_right = para_style.map(|s| s.margin_right).unwrap_or(0.0);
        let final_width = (available_width - margin_left - margin_right).max(0.0);
// ==== replace ====
        let para_style = styles.para_styles.get(para_shape_id as usize);
        let margin_left = para_style.map(|s| s.margin_left).unwrap_or(0.0);
        let margin_right = para_style.map(|s| s.margin_right).unwrap_or(0.0);
        // [claude-hwpx narrow-margin-ignore] 남는 폭이 25% 미만이면 여백을 무시한다
        let final_width = if para_style
            .is_some_and(|s| crate::renderer::style_resolver::claude_margins_ignored(s, available_width))
        {
            available_width
        } else {
            (available_width - margin_left - margin_right).max(0.0)
        };
// ==== next ====
        let para_style = styles.para_styles.get(cell_para.para_shape_id as usize);
        let margin_left = para_style.map(|s| s.margin_left).unwrap_or(0.0);
        let margin_right = para_style.map(|s| s.margin_right).unwrap_or(0.0);
        let final_width = (available_width - margin_left - margin_right).max(0.0);
// ==== replace ====
        let para_style = styles.para_styles.get(cell_para.para_shape_id as usize);
        let margin_left = para_style.map(|s| s.margin_left).unwrap_or(0.0);
        let margin_right = para_style.map(|s| s.margin_right).unwrap_or(0.0);
        // [claude-hwpx narrow-margin-ignore] 남는 폭이 25% 미만이면 여백을 무시한다
        let final_width = if para_style
            .is_some_and(|s| crate::renderer::style_resolver::claude_margins_ignored(s, available_width))
        {
            available_width
        } else {
            (available_width - margin_left - margin_right).max(0.0)
        };
