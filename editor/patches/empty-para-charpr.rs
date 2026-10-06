// ==== find ====
    let fallback_font_size = if para.text.is_empty() {
        para.char_shapes
            .first()
            .and_then(|char_shape| styles.char_styles.get(char_shape.char_shape_id as usize))
            .map(|style| style.font_size)
// ==== replace ====
    let fallback_font_size = if para.text.is_empty() {
        // [claude-hwpx empty-para-charpr] 글자 모양이 없으면 0번 글자 모양(한/글과 같게)
        para.char_shapes
            .first()
            .and_then(|char_shape| styles.char_styles.get(char_shape.char_shape_id as usize))
            .or_else(|| para.char_shapes.is_empty().then(|| styles.char_styles.first()).flatten())
            .map(|style| style.font_size)
// ==== next ====
            // 치수를 복사하면 TAC 그림 높이까지 상속되므로 vpos 원점만 보존한다.
            let font_size = para
                .char_shapes
                .first()
                .and_then(|char_shape| styles.char_styles.get(char_shape.char_shape_id as usize))
                .map(|style| style.font_size)
// ==== replace ====
            // 치수를 복사하면 TAC 그림 높이까지 상속되므로 vpos 원점만 보존한다.
            // [claude-hwpx empty-para-charpr] 글자 모양이 하나도 없는 문단(run 없는 `<hp:p>`)은 한/글이 글자 모양 0 의
            // 크기로 줄을 만든다(한국문화 14단원: 0번 10pt → 한/글 재저장 줄 1000, 종전 12px = 900)
            let font_size = para
                .char_shapes
                .first()
                .and_then(|char_shape| styles.char_styles.get(char_shape.char_shape_id as usize))
                .or_else(|| para.char_shapes.is_empty().then(|| styles.char_styles.first()).flatten())
                .map(|style| style.font_size)
