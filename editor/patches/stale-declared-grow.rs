// ==== find ====

pub fn fit_measured_table_to_declared_height(
    measured: &MeasuredTable,
    table: &Table,
    dpi: f64,
) -> MeasuredTable {
    let mut fitted = measured.clone();
    if fitted.row_heights.is_empty() || table.common.height == 0 {
        return fitted;
// ==== replace ====

/// [claude-hwpx stale-declared-grow] 표 선언 높이(hp:sz height)를 증거로 쓸 수 없는 표인가.
///
/// 한/글은 표를 열 때 행 높이를 max(칸 선언 높이, 내용)으로 다시 재고 표 높이는 그 합으로 다시 적는다 — 표 선언 높이는
/// 읽지 않는다. 한국문화 12단원(삽화 삽입 스크립트가 칸 내용을 바꾸고 줄 배치를 지운 판)의 1×1 표는 선언 58275 인데
/// 한/글 재저장본은 32423 이고 칸 선언(24381)은 그대로였다(2026-10-06). rhwp 는 선언을 하한으로 써서 마지막 행을
/// 늘려(777px) 표가 다음 쪽으로 밀리고 쪽수가 6 → 9 가 됐다.
/// 한/글이 저장한 표는 모든 칸 문단에 줄 배치가 있고 선언이 그 내용으로 잰 값이라 종전대로 믿는다. 칸 문단에 줄 배치가
/// 빠진 것이 하나라도 있으면 그 표의 내용은 선언을 적은 뒤에 바뀐 것이므로 선언에 맞추지 않는다.
/// 열 때 엔진이 빈 줄 배치를 합성해 채우므로(합성 줄은 `TAG_IMPLEMENTATION_PROPERTY`) 그 표식으로도 가린다.
pub fn claude_declared_height_stale(table: &Table) -> bool {
    use crate::model::paragraph::LineSeg;
    table.cells.iter().any(|cell| {
        cell.paragraphs.iter().any(|p| {
            p.line_segs.is_empty()
                || p.line_segs.iter().all(|s| s.tag & LineSeg::TAG_IMPLEMENTATION_PROPERTY != 0)
        })
    })
}

pub fn fit_measured_table_to_declared_height(
    measured: &MeasuredTable,
    table: &Table,
    dpi: f64,
) -> MeasuredTable {
    let mut fitted = measured.clone();
    if fitted.row_heights.is_empty() || table.common.height == 0 {
        return fitted;
    }
    // [claude-hwpx stale-declared-grow]
    if claude_declared_height_stale(table) {
        return fitted;
// ==== next ====
            && common_h > raw_table_height + 0.5
            && {
// ==== replace ====
            && common_h > raw_table_height + 0.5
            // [claude-hwpx stale-declared-grow] 한/글이 선언을 최소 높이로 지키는 것은 칸 내용이 저장 줄 배치를 가질 때뿐이다
            && !claude_declared_height_stale(table)
            && {
