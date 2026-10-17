// ==== find ====
pub(crate) fn char_width_decision<'a>(
// ==== replace ====
/// [claude-hwpx hft-symbol-widths] 한/글 2024 에서 잰 한컴 내장(HFT) 글꼴의 기호 폭(em). 글꼴 파일이 없어 내장 표와 어림이 틀리던 것
/// (test/conformance/lab e5: 한/글 PDF 글자 위치, 10pt 한글 사이 12회 중앙값).
fn claude_hft_symbol_em(font_family: &str, c: char) -> Option<f64> {
    let primary = font_family
        .split(',')
        .next()
        .unwrap_or("")
        .trim()
        .trim_matches('\'')
        .trim_matches('"');
    match (primary, c) {
        ("휴먼명조", '\u{00B7}' | '\u{2026}' | '\u{201C}' | '\u{201D}' | '\u{2018}' | '\u{2019}') => Some(1.0),
        ("휴먼명조", '\u{2014}') => Some(0.879),
        _ => None,
    }
}

pub(crate) fn char_width_decision<'a>(
// ==== next ====
    let dash_leader = is_dash_leader_run(chars, i);
// ==== replace ====
    // [claude-hwpx hft-symbol-widths] 실측 기호 폭이 있으면 그것을 쓴다
    let (base_width_raw, width_source) = match claude_hft_symbol_em(&style.font_family, c) {
        Some(em) => (font_size * em, "hftMeasuredSymbol"),
        None => (base_width_raw, width_source),
    };
    let dash_leader = is_dash_leader_run(chars, i);
// ==== next ====
        // 비례폰트의 .notdef 위장 전각(≈20px) 이 아니라 narrow(0.3em ≈ 6px) 여야 함.
        assert!(
            dot_advance <= style.font_size * 0.4,
// ==== replace ====
        // [claude-hwpx hft-symbol-widths] 한/글 2024 는 휴먼명조 `·` 를 전각으로 조판한다(lab e5). upstream 의 narrow 기대는 옛 한/글 PDF 기준.
        assert!(
            dot_advance >= style.font_size * 0.95,
