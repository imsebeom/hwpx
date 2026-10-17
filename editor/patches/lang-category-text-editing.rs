// ==== find ====
        x += *positions.last()?;
// ==== replace ====
        // [claude-hwpx lang-category] 배치 경로(paragraph_layout)는 지나간 글자 묶음을 반올림한 폭(estimate_text_width)으로 쌓는다.
        // 문장 부호가 라틴 묶음으로 갈리며 묶음이 늘어 반올림 차이가 쌓이므로 같은 식으로 더한다(issue3137 시험).
        let _ = positions.last()?;
        x += crate::renderer::layout::estimate_text_width(&run.text, &style);
