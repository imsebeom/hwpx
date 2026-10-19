// ==== find ====
                let mut claude_prev_after: i32 = 0;
// ==== replace ====
                let mut claude_prev_after: i32 = 0;
                // [claude-hwpx synth-vpos-absorb] 앞 문단이 표만 담은 문단 기준 자리 차지 표 호스트면 이 문단 위 간격은 표 아래에 묻힌다
                let mut claude_prev_float_host = false;
// ==== next ====
                        running_vpos += claude_prev_after
                            + claude_hu(claude_style.map(|s| s.spacing_before).unwrap_or(0.0));
// ==== replace ====
                        running_vpos += claude_prev_after
                            + if claude_prev_float_host {
                                0
                            } else {
                                claude_hu(claude_style.map(|s| s.spacing_before).unwrap_or(0.0))
                            };
// ==== next ====
                    claude_prev_after = if claude_table_only_host || para.line_segs.is_empty() {
// ==== replace ====
                    claude_prev_float_host = claude_table_only_host
                        && para.controls.iter().any(|c| {
                            matches!(c, Control::Table(t)
                                if !t.common.treat_as_char
                                    && matches!(t.common.vert_rel_to, crate::model::shape::VertRelTo::Para))
                        });
                    claude_prev_after = if claude_table_only_host || para.line_segs.is_empty() {
