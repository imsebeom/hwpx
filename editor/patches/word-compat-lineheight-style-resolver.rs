// ==== find ====
    pub shade_color: ColorRef,
}
// ==== replace ====
    pub shade_color: ColorRef,
    /// [claude-hwpx word-compat-lineheight] Word 호환 문서(compatibleDocument targetProgram=MS_WORD 에 adjustLineheightToFont)의 글자 모양인가.
    /// 비율 간격 줄의 높이를 글꼴 파일의 세로 수치로 잡는다(line_breaking `claude_word_line_metrics`). 문서 전체가 같은 값이다
    pub claude_word_compat: bool,
}
// ==== next ====
            font_family: String::new(),
            font_families: Vec::new(),
// ==== replace ====
            font_family: String::new(),
            claude_word_compat: false, // [claude-hwpx word-compat-lineheight]
            font_families: Vec::new(),
// ==== next ====
    ResolvedCharStyle {
        font_family,
        font_families,
        font_size,
// ==== replace ====
    ResolvedCharStyle {
        font_family,
        font_families,
        font_size,
        // [claude-hwpx word-compat-lineheight]
        claude_word_compat: doc_info.hwpx_head_tail.as_deref().is_some_and(|tail| {
            tail.contains("targetProgram=\"MS_WORD\"") && tail.contains("<hh:adjustLineheightToFont/>")
        }),
