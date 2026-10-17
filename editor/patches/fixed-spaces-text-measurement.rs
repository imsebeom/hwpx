// ==== find ====
    if c == '\u{2007}' {
        let base_width_px = font_size * 0.5;
// ==== replace ====
    // [claude-hwpx fixed-spaces] 한/글 2024: 고정폭 빈칸(fwSpace → U+2007)은 0.25em, 묶음 빈칸(nbSpace → U+00A0)은 0.5em(lab e26, 글꼴과 설정 무관)
    if c == '\u{2007}' || c == '\u{00A0}' {
        let base_width_px = font_size * if c == '\u{2007}' { 0.25 } else { 0.5 };
