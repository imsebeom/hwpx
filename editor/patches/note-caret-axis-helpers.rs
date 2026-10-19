// ==== find ====
pub(crate) fn caret_control_slots(para: &Paragraph) -> Vec<Option<usize>> {
// ==== replace ====
/// [claude-hwpx note-caret-axis] 각주, 미주 표지의 캐럿 자리(각주를 세지 않는 에디터 캐럿 축). 컨트롤 번호로 찾는다.
pub(crate) fn claude_note_caret_positions(para: &Paragraph) -> Vec<(usize, usize)> {
    let mut out = Vec::new();
    let mut c = 0usize;
    for (ci, is_caret, _) in caret_axis_items(para) {
        let is_note = ci.is_some_and(|ci| matches!(para.controls[ci], Control::Footnote(_) | Control::Endnote(_)));
        if let (Some(ci), true) = (ci, is_note) {
            out.push((ci, c));
        }
        c += (is_caret && !is_note) as usize;
    }
    out
}

pub(crate) fn caret_control_slots(para: &Paragraph) -> Vec<Option<usize>> {
