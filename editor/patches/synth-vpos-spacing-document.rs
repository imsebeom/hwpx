// ==== find ====
                let mut prev_stored_last_vpos: i32 = 0;
// ==== replace ====
                let mut prev_stored_last_vpos: i32 = 0;
                // [claude-hwpx synth-vpos-spacing] 앞 문단의 아래 간격(HWPUNIT). 다시 조판한 문단 앞에 「앞 아래 + 이 문단 위」 간격을 둔다
                let mut claude_prev_after: i32 = 0;
// ==== next ====
                    // 문단의 첫 LINE_SEG vpos를 running_vpos로 갱신
// ==== replace ====
                    // [claude-hwpx synth-vpos-spacing] 한/글 vertpos 는 문단 위아래 간격을 품는다. 다시 조판한 문단만(저장 줄 배치는 그대로)
                    let claude_style = styles.para_styles.get(para.para_shape_id as usize);
                    let claude_hu = |px: f64| (px * 7200.0 / dpi).round() as i32;
                    if was_reflowed && !para.line_segs.is_empty() {
                        running_vpos += claude_prev_after
                            + claude_hu(claude_style.map(|s| s.spacing_before).unwrap_or(0.0));
                    }
                    // 문단의 첫 LINE_SEG vpos를 running_vpos로 갱신
// ==== next ====
                    running_vpos = inner_vpos;
                    if let Some(v) = original_last_vpos {
// ==== replace ====
                    running_vpos = inner_vpos;
                    // [claude-hwpx synth-vpos-spacing] 표만 담은 문단(위아래 배치)의 아래 간격은 한/글이 더하지 않는다
                    let claude_table_only_host = para.text.trim().is_empty()
                        && para.controls.iter().any(|c| {
                            matches!(c, Control::Table(t)
                                if !t.common.treat_as_char
                                    && matches!(t.common.text_wrap, crate::model::shape::TextWrap::TopAndBottom))
                        });
                    claude_prev_after = if claude_table_only_host || para.line_segs.is_empty() {
                        0
                    } else {
                        claude_hu(claude_style.map(|s| s.spacing_after).unwrap_or(0.0))
                    };
                    if let Some(v) = original_last_vpos {
