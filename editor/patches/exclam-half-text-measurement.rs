// ==== find ====
    let dash_leader = is_dash_leader_run(chars, i);
// ==== replace ====
    // [claude-hwpx exclam-half] 한/글은 「!」 의 폭을 글꼴과 상관없이 글자 크기의 절반으로 둔다(test/conformance/lab e15, e16).
    let (base_width_raw, width_source) = if c == '!' {
        (font_size * 0.5, "hancomExclamHalf")
    } else {
        (base_width_raw, width_source)
    };
    let dash_leader = is_dash_leader_run(chars, i);
