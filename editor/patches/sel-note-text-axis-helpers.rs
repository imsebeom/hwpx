// ==== find ====
pub(crate) fn caret_control_slots(para: &Paragraph) -> Vec<Option<usize>> {
// ==== replace ====
/// [claude-hwpx sel-note-text-axis] 선택 음영용 캐럿 칸 — caret_control_slots 와 같되 각주, 미주는 칸이 아니다(에디터 캐럿 축은 각주를 세지 않는다).
pub(crate) fn claude_caret_slots_no_notes(para: &Paragraph) -> Vec<Option<usize>> {
    let mut slots = vec![None; para.controls.len()];
    let mut c = 0usize;
    for (ci, is_caret, _) in caret_axis_items(para) {
        let is_caret = is_caret
            && !ci.is_some_and(|ci| matches!(para.controls[ci], Control::Footnote(_) | Control::Endnote(_)));
        if let (Some(ci), true) = (ci, is_caret) {
            slots[ci] = Some(c);
        }
        c += is_caret as usize;
    }
    slots
}

pub(crate) fn caret_control_slots(para: &Paragraph) -> Vec<Option<usize>> {
// ==== next ====
        .filter(|(pos, ctrl)| **pos < utf16_pos && ctrl.is_logical_inline())
// ==== replace ====
        // [claude-hwpx sel-note-text-axis] 각주, 미주는 캐럿 칸이 아니다 — 세면 각주 뒤 줄 시작이 한 칸씩 밀린다
        .filter(|(pos, ctrl)| {
            **pos < utf16_pos
                && ctrl.is_logical_inline()
                && !matches!(ctrl, Control::Footnote(_) | Control::Endnote(_))
        })
