// ==== find ====
            } else {
                st.current_height += pre_height + table_total_height;
            }
        }
        // [#2243 진단] TAC 표 라인 회계 분해
// ==== replace ====
            } else {
                // [claude-hwpx empty-host-no-after] 줄 배치 없는 빈 문단의 위아래 배치 표 하나는 잰 높이에서 문단 아래 간격을 뺀다. 한/글은 표만 담은
                // 문단의 아래 간격을 더하지 않는다(정답본 15건 중 15건). 선언 높이는 생성기 값이 낡을 수 있어 쓰지 않는다
                let claude_empty_host = is_para_topbottom_float(&table.common)
                    && !para_has_non_whitespace_text(para)
                    && crate::renderer::para_has_no_stored_line_segs(para)
                    && para.controls.iter().filter(|control| matches!(control, Control::Table(_))).count() == 1;
                let claude_after = if claude_empty_host { fmt.spacing_after.min(table_total_height).max(0.0) } else { 0.0 };
                st.current_height += pre_height + table_total_height - claude_after;
            }
        }
        // [#2243 진단] TAC 표 라인 회계 분해
