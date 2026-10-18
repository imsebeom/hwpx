// ==== find ====
fn flow_inline_controls(para: &Paragraph) -> Vec<FlowInlineControl> {
    let text_len = para.text.chars().count();
    para.controls
        .iter()
        .zip(para.control_text_positions())
        .filter_map(|(control, char_position)| {
// ==== replace ====
fn flow_inline_controls(para: &Paragraph, styles: &ResolvedStyleSet) -> Vec<FlowInlineControl> {
    let text_len = para.text.chars().count();
    para.controls
        .iter()
        .zip(para.control_text_positions())
        .filter_map(|(control, char_position)| {
            // [claude-hwpx char-overlap-width] 동그라미 겹친 글자는 그 자리 글자 모양의 「◯」 폭(장평 반영, 자간 빼고)만큼 차지한다(d113 한/글 PDF 실측)
            if let Control::CharOverlap(overlap) = control {
                if overlap.border_type != 1 || char_position >= text_len {
                    return None;
                }
                let utf16 = para.char_offsets.get(char_position).copied().unwrap_or(char_position as u32);
                let style_id = super::find_active_char_shape(&para.char_shapes, utf16);
                let mut ts = crate::renderer::layout::resolved_to_text_style(
                    styles,
                    style_id,
                    crate::renderer::style_resolver::detect_lang_category('\u{25EF}'),
                );
                ts.letter_spacing = 0.0;
                let width_hwp = (estimate_text_width_unrounded("\u{25EF}", &ts) * 75.0).round() as i32;
                return Some(FlowInlineControl { char_position, width_hwp, height_hwp: 0, baseline_distance_hwp: None });
            }
// ==== next ====
    let text_chars = para.text.chars().collect::<Vec<_>>();
    let inline_controls = flow_inline_controls(para);
// ==== replace ====
    let text_chars = para.text.chars().collect::<Vec<_>>();
    let inline_controls = flow_inline_controls(para, styles); // [claude-hwpx char-overlap-width]
// ==== next ====
    // inline token: it is represented by the caller's exclusion instead.
    let inline_controls = flow_inline_controls(para);
// ==== replace ====
    // inline token: it is represented by the caller's exclusion instead.
    let inline_controls = flow_inline_controls(para, styles); // [claude-hwpx char-overlap-width]
// ==== next ====
    let text_len = text_chars.len();
    let inline_controls = flow_inline_controls(para);
// ==== replace ====
    let text_len = text_chars.len();
    let inline_controls = flow_inline_controls(para, styles); // [claude-hwpx char-overlap-width]
