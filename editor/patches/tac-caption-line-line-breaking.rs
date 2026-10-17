// ==== find ====
fn inline_control_line_height_hwp(para: &Paragraph) -> Option<i32> {
// ==== replace ====
/// [claude-hwpx tac-caption-line] 글자처럼 취급 표를 담은 줄 높이: 표 높이 + 바깥 여백 위아래 + 위, 아래 캡션(높이 + 캡션 간격).
/// 한/글 재저장 d242: 8412 + 283×2 + 1000 + 283 = 10261. 왼쪽, 오른쪽 캡션은 높이에 들지 않는다.
fn claude_tac_table_line_height_hwp(table: &crate::model::table::Table) -> i32 {
    let base = table.common.height as i32
        + table.outer_margin_top as i32
        + table.outer_margin_bottom as i32;
    let Some(caption) = table.caption.as_ref() else {
        return base;
    };
    if matches!(
        caption.direction,
        crate::model::shape::CaptionDirection::Left | crate::model::shape::CaptionDirection::Right
    ) {
        return base;
    }
    // dpi 를 HWPUNIT 의 인치당 값(7200)으로 주면 px 대신 HWPUNIT 이 나온다
    let caption_hu = crate::renderer::composer::caption_height_px(&table.caption, 7200.0).round() as i32;
    if caption_hu <= 0 {
        return base;
    }
    base + caption_hu + caption.spacing as i32
}

fn inline_control_line_height_hwp(para: &Paragraph) -> Option<i32> {
// ==== next ====
            Control::Table(table) if table.common.treat_as_char => Some(
                table.common.height as i32
                    + table.outer_margin_top as i32
                    + table.outer_margin_bottom as i32,
            ),
// ==== replace ====
            Control::Table(table) if table.common.treat_as_char => {
                Some(claude_tac_table_line_height_hwp(table))
            }
// ==== next ====
            (
                width,
                table.common.height as i32
                    + table.outer_margin_top as i32
                    + table.outer_margin_bottom as i32,
            )
// ==== replace ====
            (width, claude_tac_table_line_height_hwp(table))
// ==== next ====
            Control::Table(t) if t.common.treat_as_char => Some(
                (t.common.height as i32)
                    .saturating_add(i32::from(t.outer_margin_top))
                    .saturating_add(i32::from(t.outer_margin_bottom)),
            ),
// ==== replace ====
            Control::Table(t) if t.common.treat_as_char => Some(claude_tac_table_line_height_hwp(t)),
