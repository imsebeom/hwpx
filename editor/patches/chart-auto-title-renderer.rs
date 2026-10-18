// ==== find ====
    let effective_title: Option<String> = chart.title.clone().or_else(|| {
        (chart.has_title_elem && !chart.auto_title_deleted).then(|| match &chart.series[..] {
// ==== replace ====
    // [claude-hwpx chart-auto-title] c:title 요소가 없어도 이름 있는 계열이 하나면 한/글은 그 이름을 제목으로 그린다(빌더 차트, 한/글 PDF 실측)
    let claude_single_named = matches!(&chart.series[..], [only] if !only.name.is_empty());
    let effective_title: Option<String> = chart.title.clone().or_else(|| {
        ((chart.has_title_elem || claude_single_named) && !chart.auto_title_deleted).then(|| match &chart.series[..] {
// ==== next ====
                    name: name.to_string(),
                    values: vec![1.0, 2.0, 3.0],
                    series_type: OoxmlChartType::Pie,
                    ..Default::default()
                }],
                categories: vec!["가".into(), "나".into(), "다".into()],
                ..Default::default()
// ==== replace ====
                    name: name.to_string(),
                    values: vec![1.0, 2.0, 3.0],
                    series_type: OoxmlChartType::Pie,
                    ..Default::default()
                }],
                categories: vec!["가".into(), "나".into(), "다".into()],
                // [claude-hwpx chart-auto-title] 이름 있는 단일 계열은 자동 제목이 붙으므로 범례 자리만 비교하게 제목을 끈다
                auto_title_deleted: true,
                ..Default::default()
