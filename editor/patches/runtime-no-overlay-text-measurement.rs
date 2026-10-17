// ==== find ====
        let is_halfwidth_punct = matches!(c, '\u{2018}'..='\u{2027}');
// ==== replace ====
        // [claude-hwpx runtime-no-overlay] 실행 중 등록한 표(entry_index = usize::MAX: 글꼴 파일, 한/글 실측)의 폭은 한/글 2024 가 그대로 쓴다(lab e20)
        let runtime_metric = mm.entry_index == usize::MAX;
        let is_halfwidth_punct = !runtime_metric && matches!(c, '\u{2018}'..='\u{2027}');
// ==== next ====
pub(crate) fn area_dot_fallback_width(font_family: &str, font_size: f64) -> Option<f64> {
    let fam = font_family.split(',').next().unwrap_or("").trim();
// ==== replace ====
pub(crate) fn area_dot_fallback_width(font_family: &str, font_size: f64) -> Option<f64> {
    let fam = font_family.split(',').next().unwrap_or("").trim();
    // [claude-hwpx runtime-no-overlay] 실행 중 등록한 표에 ㆍ 가 있으면 그 폭을 쓴다(한/글 2024 는 파일 폭, 글꼴 12종 모두 1em)
    if font_metrics_data::find_metric_decision(fam.trim_matches('\'').trim_matches('"'), false, false)
        .is_some_and(|mm| mm.entry_index == usize::MAX && mm.metric.get_width('\u{318D}').is_some())
    {
        return None;
    }
// ==== next ====
        let is_narrow_unicode_punct = matches!(c, '\u{2018}' | '\u{2019}' | '\u{2027}');
        let is_b7_notdef_artifact =
            c == '\u{00B7}' && glyph_w >= mm.metric.em_size && !is_monospace_metric(mm.metric);
// ==== replace ====
        let is_narrow_unicode_punct =
            !runtime_metric && matches!(c, '\u{2018}' | '\u{2019}' | '\u{2027}');
        let is_b7_notdef_artifact = !runtime_metric
            && c == '\u{00B7}'
            && glyph_w >= mm.metric.em_size
            && !is_monospace_metric(mm.metric);
