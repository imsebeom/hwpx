// ==== find ====
    estimate_text_width, estimate_text_width_unrounded, hancom_regenerated_space_width,
// ==== replace ====
    // [claude-hwpx hancom-quantum] 이 파일의 글자 폭은 아래 같은 이름의 함수(한/글 4단위 폭)를 거친다
    estimate_text_width, estimate_text_width_unrounded as estimate_text_width_unrounded_exact,
    hancom_regenerated_space_width,
// ==== next ====
fn to_hwp(px: f64) -> i32 {
    (px * 75.0) as i32
}
// ==== replace ====
// 4 HWPUNIT 배수로 맞춘 폭은 px 로 갔다 와도 같은 정수여야 한다(버림만 하면 871.9999 가 871 이 된다).
fn to_hwp(px: f64) -> i32 {
    (px * 75.0 + 1e-6).floor() as i32
}

/// 글자 하나의 줄 나눔용 폭. 한/글 규칙(4 HWPUNIT 단위)을 적용할 수 없는 글자는 종전 실수 폭.
fn estimate_text_width_unrounded(text: &str, style: &crate::renderer::TextStyle) -> f64 {
    let mut chars = text.chars();
    if let (Some(ch), None) = (chars.next(), chars.next()) {
        if let Some(px) = crate::renderer::layout::claude_hancom_advance_px(ch, style) {
            return px;
        }
    }
    estimate_text_width_unrounded_exact(text, style)
}
// ==== next ====
const LINE_BREAK_TOLERANCE: i32 = 15;
// ==== replace ====
// 폭을 한/글과 같은 4 단위로 재므로 여유를 두지 않는다(실측: 자리와 같으면 담고 4 넘으면 꺾는다).
const LINE_BREAK_TOLERANCE: i32 = 0;
// ==== next ====
            // [#5678] `TextStyle` 을 통째로 만들지 않고 자간만 읽는다.
            resolved_letter_spacing(styles, style_id, lang)
// ==== replace ====
            // [#5678] `TextStyle` 을 통째로 만들지 않고 자간만 읽는다.
            let em_spacing = resolved_letter_spacing(styles, style_id, lang);
            if em_spacing == 0.0 {
                return 0.0;
            }
            // 줄 끝 글자에서 빼는 자간은 그 글자 폭에 실제로 더한 값이어야 한다(글자 폭 비례, 4 단위)
            let style = resolved_to_text_style(styles, style_id, lang);
            crate::renderer::layout::claude_hancom_spacing_px(*ch, &style).unwrap_or(em_spacing)
