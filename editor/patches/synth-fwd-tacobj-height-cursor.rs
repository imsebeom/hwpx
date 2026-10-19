// ==== find ====
        if synthetic_prev_seg
            && result > y_offset + 0.5
            && result - y_offset <= SYNTH_FORWARD_REANCHOR_MIN_PX
        {
// ==== replace ====
        // [claude-hwpx synth-fwd-tacobj] 앞 문단이 글 없이 글자처럼 취급 개체만 든 줄이면 순차 y 가 그 줄 높이를 빠뜨린다 — 막지 않는다(d333 p0)
        let claude_prev_tac_object_line = !para_has_visible_text(prev_para)
            && prev_para.controls.iter().any(|c| match c {
                Control::Shape(s) => s.common().treat_as_char,
                Control::Picture(p) => p.common.treat_as_char,
                _ => false,
            });
        if synthetic_prev_seg
            && !claude_prev_tac_object_line
            && result > y_offset + 0.5
            && result - y_offset <= SYNTH_FORWARD_REANCHOR_MIN_PX
        {
