// ==== find ====
fn claude_bullet_advance_hwp(para: &Paragraph, styles: &ResolvedStyleSet) -> Option<i32> {
// ==== replace ====
fn claude_bullet_advance_hwp(para: &Paragraph, styles: &ResolvedStyleSet) -> Option<i32> {
    // [claude-hwpx bullet-place] 자동 내어쓰기를 켠 글머리표만(모든 줄을 좁힌다). 끈 글머리표는 번호 문단처럼 첫 줄만 좁힌다(reflow)
    claude_bullet_head_hwp(para, styles)
        .filter(|(_, auto)| *auto)
        .map(|(advance, _)| advance)
}

/// [claude-hwpx bullet-place] 글머리표 문단의 (표식 자리 HWPUNIT, 자동 내어쓰기). 그리기(paragraph_layout)도 같은 값을 쓴다
pub(crate) fn claude_bullet_head_hwp(
    para: &Paragraph,
    styles: &ResolvedStyleSet,
) -> Option<(i32, bool)> {
// ==== next ====
    if !auto_indent {
        return None;
    }
    let char_style_id = if (bullet.char_shape_id as usize) < styles.char_styles.len() {
// ==== replace ====
    // [claude-hwpx bullet-place] 자동 내어쓰기를 끈 글머리표도 자리를 돌려준다(종전 None)
    let char_style_id = if (bullet.char_shape_id as usize) < styles.char_styles.len() {
// ==== next ====
    Some(advance + i32::from(bullet.width_adjust))
}
// ==== replace ====
    Some((advance + i32::from(bullet.width_adjust), auto_indent))
}
// ==== next ====
        match claude_number_head_hwp(para, styles).filter(|(advance, _)| *advance > 0 && *advance < seg_width_hwp) {
// ==== replace ====
        match claude_number_head_hwp(para, styles)
            .or_else(|| claude_bullet_head_hwp(para, styles).filter(|(_, auto)| !*auto))
            .filter(|(advance, _)| *advance > 0 && *advance < seg_width_hwp)
        {
