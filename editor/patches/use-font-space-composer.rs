// ==== find ====
fn regenerated_half_space_width(style: &TextStyle) -> f64 {
// ==== replace ====
fn regenerated_half_space_width(style: &TextStyle) -> f64 {
    // [claude-hwpx use-font-space] 「글꼴에 어울리는 빈칸」이 켜진 글자 모양은 반각 칸이 아니라 글꼴 고유 폭이다.
    if style.use_font_space {
        return estimate_text_width_unrounded(" ", style);
    }
