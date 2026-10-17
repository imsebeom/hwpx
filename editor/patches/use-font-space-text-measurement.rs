// ==== find ====
pub(crate) fn hancom_regenerated_space_width(style: &TextStyle) -> Option<f64> {
// ==== replace ====
pub(crate) fn hancom_regenerated_space_width(style: &TextStyle) -> Option<f64> {
    // [claude-hwpx use-font-space] 반각 공백은 「글꼴에 어울리는 빈칸」이 꺼진 글자 모양의 규칙이다. 켜져 있으면 글꼴 고유 폭 그대로.
    if style.use_font_space {
        return None;
    }
// ==== next ====
    let dash_leader = is_dash_leader_run(chars, i);
// ==== replace ====
    // [claude-hwpx use-font-space-own] 폭 표는 빈칸을 반각(또는 한컴 PDF 실측값)으로 바꿔 돌려준다. 이는 「글꼴에
    // 어울리는 빈칸」이 꺼진 글자 모양의 규칙이고, 켜져 있으면 한/글은 글꼴 파일의 빈칸 폭을 쓴다(한/글 2024 실측:
    // 맑은 고딕 720/2048, 함초롬바탕 300/1000, 굴림 341/1024 em 이 PDF 글자 위치와 맞음 — test/conformance/lab e1).
    let (base_width_raw, width_source) = match (c, style.use_font_space, width_source, metric) {
        (' ', true, "metricHalfSpace" | "metricSpaceOverlay", Some(lookup)) => lookup
            .metric
            .get_width(' ')
            .map(|w| (f64::from(w) * font_size / f64::from(lookup.metric.em_size), "metricFontSpace"))
            .unwrap_or((base_width_raw, width_source)),
        _ => (base_width_raw, width_source),
    };
    let dash_leader = is_dash_leader_run(chars, i);
// ==== next ====
            kerning: cs.kerning,
            // 단일 출처
// ==== replace ====
            kerning: cs.kerning,
            use_font_space: cs.use_font_space,
            // 단일 출처
