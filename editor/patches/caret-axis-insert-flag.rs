
// [claude-hwpx caret-axis] 글자 삽입이 같은 글자 위치의 인라인 컨트롤 뒤에 들어가게 하는 표지.
// 스튜디오가 캐럿이 글자처럼 취급 개체 바로 뒤일 때만 켜고, 삽입 호출이 끝나면 끈다(wasm 은 단일 스레드).
thread_local! {
    pub static INSERT_AFTER_INLINE_CONTROLS: std::cell::Cell<bool> = const { std::cell::Cell::new(false) };
}

