// ==== find ====
    let visible_top = paragraph_top.saturating_add(signed_hwpunit(common.vertical_offset));
    let horizontal = visible_left.saturating_sub(i32::from(common.margin.left))
// ==== replace ====
    // [claude-hwpx wrap-margin-box] 한글은 거리와 정렬로 바깥 여백까지 포함한 상자를 놓고 그림을 여백만큼 안쪽에 그린다
    // (한글 PDF 실측: 왼쪽 정렬 그림이 단 왼쪽 + 1mm, 오른쪽 정렬은 단 오른쪽 - 1mm, 세로 거리 0 은 문단 윗변 + 1mm).
    // 종전에는 거리가 그림 자체를 놓아 비키는 영역이 여백만큼 위, 왼쪽으로 치우쳐 한 줄을 먼저 좁혔다
    let visible_left = visible_left.saturating_add(claude_margin_box_shift_x(common));
    let visible_top = paragraph_top
        .saturating_add(signed_hwpunit(common.vertical_offset))
        .saturating_add(i32::from(common.margin.top));
    let horizontal = visible_left.saturating_sub(i32::from(common.margin.left))
// ==== next ====
    .saturating_add(vertical_offset);
    let horizontal = if top_and_bottom {
// ==== replace ====
    .saturating_add(vertical_offset)
    .saturating_add(i32::from(common.margin.top));
    let visible_left = visible_left.saturating_add(claude_margin_box_shift_x(common));
    let horizontal = if top_and_bottom {
// ==== next ====
pub(crate) fn resolve_picture_exclusion(
// ==== replace ====
/// [claude-hwpx wrap-margin-box] 여백 상자를 정렬했을 때 그림 왼쪽이 그림 자체를 정렬했을 때보다 얼마나 옮겨지는가
fn claude_margin_box_shift_x(common: &crate::model::shape::CommonObjAttr) -> i32 {
    let (left, right) = (i32::from(common.margin.left), i32::from(common.margin.right));
    match common.horz_align {
        HorzAlign::Left | HorzAlign::Inside => left,
        HorzAlign::Center => (left - right) / 2,
        HorzAlign::Right | HorzAlign::Outside => -right,
    }
}

pub(crate) fn resolve_picture_exclusion(
