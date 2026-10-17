// ==== find ====
        let embedded = measure_char_width_embedded_decision(
            &style.font_family,
            style.bold,
// ==== replace ====
        // [claude-hwpx bold-regular-width] 한/글은 굵은 글자도 보통 글꼴의 폭으로 조판한다(test/conformance/lab e10, e11). 그리기만 굵게.
        let embedded = measure_char_width_embedded_decision(
            &style.font_family,
            false,
