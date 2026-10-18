// ==== find ====
            let cap = if ladder_omits_spacing || ladder_matches_total {
                fmt.total_height
            } else {
                cap
            };
// ==== replace ====
            // [claude-hwpx tac-cap-synth] 엔진이 만든 줄의 HWPX 문단은 줄 높이 + 줄 간격 전체로 전진한다(harvest_tacstep.py: 한/글 1,685건 모두 전체,
            // cap 과 맞는 것 0건). 저장 사다리 증거(위 두 판정)가 없어 cap 이 표마다 줄 간격 절반을 깎았다(d193)
            // 줄 하나뿐인(표만 든) 문단만 — 글 줄이 앞에 있으면 표가 다음 쪽으로 갈 때 fmt.total 이 앞 쪽 글 줄까지 품는다(d043 p6)
            let claude_synth_hwpx = st.profile.hwpx_container()
                && para.line_segs.len() == 1
                && !para_has_visible_text(para)
                && para.line_segs.first().is_some_and(|s| {
                    s.tag & crate::model::paragraph::LineSeg::TAG_IMPLEMENTATION_PROPERTY != 0
                });
            let cap = if ladder_omits_spacing || ladder_matches_total || claude_synth_hwpx {
                fmt.total_height
            } else {
                cap
            };
// ==== next ====
        if table.common.treat_as_char
            && fmt.line_heights.len() == 1
            && fmt.total_height > table_total
        {
            table_total = fmt.total_height;
        }
// ==== replace ====
        if table.common.treat_as_char
            && fmt.line_heights.len() == 1
            && fmt.total_height > table_total
        {
            table_total = fmt.total_height;
        }
        // [claude-hwpx tac-cap-synth] 한 줄짜리 글자처럼 취급 표가 쪽 끝에 들어가려면 한/글은 「위 간격 + 줄 높이」(표 + 바깥 여백)만 요구한다
        // (tac-caption-line 과 같은 마지막 줄 규칙). table_total 은 뒤 줄 간격(host_spacing.after_for_fit, 위 정합의 fmt.total)을
        // 품어, d292 p75(표 379.9px)가 남은 386.7px 에 못 들어가고 다음 쪽으로 갔다. 판정에서만 그 꼬리를 뺀다
        let claude_fit_tail = if table.common.treat_as_char && fmt.line_heights.len() == 1 {
            let need = (fmt.spacing_before + fmt.line_heights[0])
                .max(ft.effective_height + ft.host_spacing.before);
            (table_total - need).max(0.0)
        } else {
            0.0
        };
// ==== next ====
        let whole_fit_table_total = if uses_painted_row_footprint_for_whole_fit {
            table_total.max(measured_row_table_height.unwrap_or(0.0) + host_spacing_total)
        } else {
            table_total
        };
// ==== replace ====
        let whole_fit_table_total = if uses_painted_row_footprint_for_whole_fit {
            table_total.max(measured_row_table_height.unwrap_or(0.0) + host_spacing_total)
        } else {
            // [claude-hwpx tac-cap-synth] 한 줄짜리 글자처럼 취급 표의 뒤 간격은 들어감 판정에서 뺀다(위 claude_fit_tail)
            table_total - claude_fit_tail
        };
// ==== next ====
                let overflow_threshold = if prev_is_table {
// ==== replace ====
                // [claude-hwpx tac-cap-synth] 글 없이 글자처럼 취급 개체만 든 문단도 마지막 줄 뒤 줄 간격 없이 들어가면 된다(표 경로와 같은 마지막 줄 규칙).
                // 앞 표들이 한/글만큼 내려가자 d034 p400(그룹 개체 줄 17383, 남은 자리에 들어감)이 뒤 간격 때문에 다음 쪽으로 밀렸다.
                // 글 문단까지 넓히면 d033 이 틀려 개체만 든 문단으로 좁힌다
                let claude_object_only = st.profile.hwpx_container()
                    && !para_has_visible_text(para)
                    && para.controls.iter().any(|c| match c {
                        Control::Picture(p) => p.common.treat_as_char,
                        Control::Shape(s) => s.common().treat_as_char,
                        _ => false,
                    });
                let overflow_threshold = if prev_is_table || claude_object_only {
