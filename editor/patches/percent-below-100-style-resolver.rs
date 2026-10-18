// ==== find ====
        .map(|ps| resolve_single_para_style(ps, &doc_info.tab_defs, dpi, is_hwp3_variant))
// ==== replace ====
        .map(|ps| {
            let mut style = resolve_single_para_style(ps, &doc_info.tab_defs, dpi, is_hwp3_variant);
            // [claude-hwpx percent-below-100] HWPX 의 비율 0% 는 명시값이다(간격 = -줄 높이, 정답본 24줄). 줄 간격 계산은 0 을 결손으로 보니 아주 작은 양수로 넘긴다
            if doc_info.hwpx_head_tail.is_some()
                && matches!(ps.line_spacing_type, LineSpacingType::Percent)
                && ps.line_spacing == 0
            {
                style.line_spacing = 1e-6;
            }
            style
        })
