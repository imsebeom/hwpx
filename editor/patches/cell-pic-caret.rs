// ==== find ====
/// 캐럿 축 → 나누기 축. 캐럿 칸 `caret` 개를 지난 바로 그 자리(뒤따르는 캐럿 밖 컨트롤 앞)다.
// ==== replace ====
/// [claude-hwpx cell-pic-caret] 컨트롤 번호 → 그 컨트롤 바로 앞의 캐럿 칸. 없으면 문단 캐럿 길이.
/// 칸 안 글자처럼 취급 그림을 끌어 옮길 때 잘라 낼 자리를 찾는다(스튜디오 플러그인 installCellPicMove)
pub(crate) fn claude_control_caret_offset(para: &Paragraph, control_idx: usize) -> usize {
    let mut c = 0usize;
    for (ci, is_caret, _) in caret_axis_items(para) {
        if ci == Some(control_idx) {
            return c;
        }
        c += is_caret as usize;
    }
    c
}

/// 캐럿 축 → 나누기 축. 캐럿 칸 `caret` 개를 지난 바로 그 자리(뒤따르는 캐럿 밖 컨트롤 앞)다.
