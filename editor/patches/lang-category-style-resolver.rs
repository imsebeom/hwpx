// ==== find ====
    match cp {
        // [#2070] ㆍ(아래아, U+318D)는 한컴이 USER 스크립트 폰트로 렌더한다.
// ==== replace ====
    match cp {
        // [claude-hwpx lang-category] 한/글 2024 실측(test/conformance/lab e7, e8): 문맥과 상관없이 고정 범주다.
        // ASCII 문장 부호, Latin-1 기호, 따옴표 → 라틴. 빈칸(U+0020, U+00A0)도 한/글은 라틴이지만 앞 글자를 따르게
        // 둔다(composer.rs is_lang_neutral) — 빈칸마다 글자 묶음이 쪼개지면 그리기와 커서 예측이 어긋나고,
        // 「글꼴에 어울리는 빈칸」이 꺼진 대부분의 문서는 어느 글꼴이든 폭이 같다.
        0x0021..=0x002F | 0x003A..=0x0040 | 0x005B..=0x0060 | 0x007B..=0x007E |
        0x00A1..=0x00BF | 0x2018..=0x201F => 1,
        // 대시, 단검표, 줄임표, 퍼밀, 프라임, 참고표, ™, ℃ → 기호
        0x2013..=0x2015 | 0x2020..=0x203C | 0x2103 | 0x2122 => 5,
        // [#2070] ㆍ(아래아, U+318D)는 한컴이 USER 스크립트 폰트로 렌더한다.
// ==== next ====
        // 공백, 구두점 등은 기본값(한국어=0)
        assert_eq!(detect_lang_category(' '), 0);
        assert_eq!(detect_lang_category('.'), 0);
        assert_eq!(detect_lang_category(','), 0);
// ==== replace ====
        // [claude-hwpx lang-category] 빈칸은 기본값(호출부가 앞 글자를 따름), 문장 부호는 라틴(한/글 2024 실측, lab e7)
        assert_eq!(detect_lang_category(' '), 0);
        assert_eq!(detect_lang_category('.'), 1);
        assert_eq!(detect_lang_category(','), 1);
