// ==== find ====
    let indent_px = indent_override.unwrap_or_else(|| para_style.map(|style| style.indent).unwrap_or(0.0));
// ==== replace ====
    let indent_px = indent_override.unwrap_or_else(|| para_style.map(|style| style.indent).unwrap_or(0.0));
    // [claude-hwpx narrow-margin-ignore] 남는 폭이 25% 미만이면 들여쓰기를 무시한다(상자 폭 + 여백 = 원래 줄 폭)
    let indent_px = if para_style.is_some_and(|s| {
        let box_px = hwpunit_to_px(frame.horizontal.end - frame.horizontal.start, dpi);
        crate::renderer::style_resolver::claude_margins_ignored(s, box_px + s.margin_left + s.margin_right)
    }) {
        0.0
    } else {
        indent_px
    };
// ==== next ====
    let indent_px = claude_indent_override.unwrap_or_else(|| para_style.map(|s| s.indent).unwrap_or(0.0));
// ==== replace ====
    let indent_px = claude_indent_override.unwrap_or_else(|| para_style.map(|s| s.indent).unwrap_or(0.0));
    // [claude-hwpx narrow-margin-ignore] 남는 폭이 25% 미만이면 들여쓰기를 무시한다(상자 폭 + 여백 = 원래 줄 폭)
    let indent_px = if para_style.is_some_and(|s| {
        let box_px = hwpunit_to_px(seg_width_hwp, dpi);
        crate::renderer::style_resolver::claude_margins_ignored(s, box_px + s.margin_left + s.margin_right)
    }) {
        0.0
    } else {
        indent_px
    };
