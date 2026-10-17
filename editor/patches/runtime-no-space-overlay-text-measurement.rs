// ==== find ====
    let (w, width_source) = if c == ' ' {
        if let Some(width) = hancom_pdf_space_width(primary_name, font_size) {
// ==== replace ====
    // [claude-hwpx runtime-no-space-overlay] 실행 중 등록한 표(한/글 실측)가 있으면 한양 글꼴 빈칸 예외를 쓰지 않는다(lab e24: 한/글 2024 는 0.5em)
    let (w, width_source) = if c == ' ' {
        if let Some(width) = (mm.entry_index != usize::MAX)
            .then(|| hancom_pdf_space_width(primary_name, font_size))
            .flatten()
        {
