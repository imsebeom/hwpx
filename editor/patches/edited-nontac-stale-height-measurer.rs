// ==== find ====
pub fn claude_declared_height_stale(table: &Table) -> bool {
    use crate::model::paragraph::LineSeg;
    table.cells.iter().any(|cell| {
// ==== replace ====
pub fn claude_declared_height_stale(table: &Table) -> bool {
    use crate::model::paragraph::LineSeg;
    // [claude-hwpx edited-nontac-stale] 편집으로 내용이 바뀐 글자처럼 취급이 아닌 표의 적힌 높이도 지금 내용으로 잰 값이 아니다.
    // 한글은 칸을 고칠 때마다 표 높이를 다시 재고, 처음부터 조판한 rhwp 도 적힌 높이를 바닥으로 쓰지 않는다
    // (2026-10-25 편집 순서 시험 「긴 글 → 글자처럼 취급 끄기 → 짧은 글」). 표식은 table-height-sync 와 칸 글 편집이 켠다
    if !table.common.treat_as_char && table.text_reflowed_after_edit {
        return true;
    }
    table.cells.iter().any(|cell| {
