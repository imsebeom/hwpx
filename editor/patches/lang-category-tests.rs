// ==== find ====
    assert!(is_lang_neutral(' '));
    assert!(is_lang_neutral('.'));
    assert!(is_lang_neutral(','));
    assert!(is_lang_neutral('!'));
    assert!(is_lang_neutral('('));
// ==== replace ====
    // [claude-hwpx lang-category] 한/글은 문장 부호를 라틴 글꼴로 잰다(앞 글자를 따르지 않음, lab e7). 빈칸만 중립.
    assert!(is_lang_neutral(' '));
    assert!(!is_lang_neutral('.'));
    assert!(!is_lang_neutral(','));
    assert!(!is_lang_neutral('!'));
    assert!(!is_lang_neutral('('));
// ==== next ====
    let composed = compose_paragraph(&para);
    let run = &composed.lines[0].runs[0];
    assert_eq!(run.text, text, "원문 IR은 바꾸지 않는다");
    assert_eq!(
        run.display_text.as_deref(),
        Some("한글, 한메일, 한팩스, 한소프트, ᄒᆞᆫ겨울"),
// ==== replace ====
    let composed = compose_paragraph(&para);
    // [claude-hwpx lang-category] 쉼표가 라틴 묶음으로 갈리므로 묶음들을 이어 붙여 본다
    let runs = &composed.lines[0].runs;
    let joined: String = runs.iter().map(|run| run.text.as_str()).collect();
    assert_eq!(joined, text, "원문 IR은 바꾸지 않는다");
    let shown: String = runs
        .iter()
        .map(|run| run.display_text.as_deref().unwrap_or(run.text.as_str()))
        .collect();
    assert_eq!(
        Some(shown.as_str()),
        Some("한글, 한메일, 한팩스, 한소프트, ᄒᆞᆫ겨울"),
