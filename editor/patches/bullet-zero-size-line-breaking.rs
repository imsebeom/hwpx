// ==== find ====
    let font_size = styles
        .char_styles
        .get(char_style_id as usize)
        .map(|style| style.font_size)
        .filter(|size| *size > 0.0)?;
    // 1/1800 인치(HWPUNIT/4) 단위
    let em = font_size * 75.0 / 4.0;
    let cell = if (bullet.bullet_char as u32) < 0x80 {
// ==== replace ====
    let font_size = styles
        .char_styles
        .get(char_style_id as usize)
        .map(|style| style.font_size)
        .filter(|size| *size > 0.0)
        // [claude-hwpx bullet-zero-size] 글머리표 글자 모양 크기가 0 이면 한/글은 문단 글자 크기로 자리를 잡는다(lab e31)
        .or_else(|| {
            para.char_shapes
                .first()
                .and_then(|shape| styles.char_styles.get(shape.char_shape_id as usize))
                .map(|style| style.font_size)
                .filter(|size| *size > 0.0)
        })?;
    // 1/1800 인치(HWPUNIT/4) 단위
    let em = font_size * 75.0 / 4.0;
    let cell = if (bullet.bullet_char as u32) < 0x80 {
