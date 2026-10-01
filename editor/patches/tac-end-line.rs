// ==== find ====
    let forced_inline_line = split_stale_cell_reflow
        .then(|| {
// ==== replace ====
    // [claude-hwpx tac-end-line] 글 뒤에 글자처럼 취급 개체 하나만 붙은 문단(그림을 문단 끝에 넣거나 옮긴 칸 문단)은 칸 나누기가
    // 아니어도 그 개체를 마지막 줄에 두고, 그 줄에 안 들어가면 개체만 담은 줄을 새로 만든다(한글과 같다). 종전에는 개체가
    // 줄 흐름에서 빠지고 높이가 첫 줄에 붙어, 여러 줄 문단 끝에 그림을 넣으면 첫 줄이 벌어지고 뒤 줄이 다음 문단과 겹쳤다(2026-10-02)
    let claude_trailing_tac = {
        let tl = para.text.chars().count();
        let sized: Vec<usize> = para
            .controls
            .iter()
            .zip(para.control_text_positions())
            .filter(|(c, _)| inline_control_size_hwp(c).is_some())
            .map(|(_, p)| p)
            .collect();
        tl > 0 && sized.len() == 1 && sized[0] == tl
    };
    let forced_inline_line = (split_stale_cell_reflow || claude_trailing_tac)
        .then(|| {
// ==== next ====
    if forced_inline_line.is_none() && inline_controls.is_empty() {
        if let Some(height_hwp) = inline_control_line_height_hwp(para) {
            // 기존 인라인 TAC 개체는 해당 문단의 최초 line box에 남긴다.
            if let Some(seg) = new_line_segs.first_mut() {
                apply_inline_control_line_height(seg, height_hwp);
            }
        }
    }
// ==== replace ====
    if forced_inline_line.is_none() && inline_controls.is_empty() {
        if let Some(height_hwp) = inline_control_line_height_hwp(para) {
            // 기존 인라인 TAC 개체는 해당 문단의 최초 line box에 남긴다.
            // [claude-hwpx tac-end-line] 글 뒤에 붙은 개체 하나는 마지막 줄에 둔다(그 줄에 들어가는 경우)
            let seg = if claude_trailing_tac { new_line_segs.last_mut() } else { new_line_segs.first_mut() };
            if let Some(seg) = seg {
                apply_inline_control_line_height(seg, height_hwp);
            }
        }
    }
