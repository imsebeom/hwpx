
// [claude-hwpx caret-axis] 글자 삽입이 같은 글자 위치의 인라인 컨트롤 뒤에 들어가게 하는 표지.
// 스튜디오가 캐럿이 글자처럼 취급 개체 바로 뒤일 때만 켜고, 삽입 호출이 끝나면 끈다(wasm 은 단일 스레드).
thread_local! {
    pub static INSERT_AFTER_INLINE_CONTROLS: std::cell::Cell<bool> = const { std::cell::Cell::new(false) };
    /// [claude-hwpx insert-after-count] 표지가 켜졌을 때 같은 글자 위치의 인라인 개체 가운데 앞에 둘 개수.
    /// usize::MAX 면 전부(종전 동작). 칸 안 두 그림 사이에 글을 넣을 때 1 이 된다.
    pub static INSERT_AFTER_INLINE_COUNT: std::cell::Cell<usize> = const { std::cell::Cell::new(usize::MAX) };
}

/// [claude-hwpx insert-after-count] 캐럿 앞 인라인 개체 가운데 글자 위치 text_off 에 있는 것의 수.
pub fn claude_inline_before_at(para: &Paragraph, caret: usize, text_off: usize) -> usize {
    let before = para
        .controls
        .iter()
        .zip(para.control_text_positions())
        .filter(|(c, p)| *p < text_off && c.is_logical_inline())
        .count();
    caret.saturating_sub(text_off).saturating_sub(before)
}

