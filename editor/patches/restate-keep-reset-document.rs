// ==== find ====
                seg.line_height = new_lh;
                seg.text_height = new_lh;
                doc.claude_shift_following_vpos(si, pi, old_end);
                doc.recompose_paragraph(si, pi);
// ==== replace ====
                let claude_delta = new_lh - seg.line_height;
                seg.line_height = new_lh;
                seg.text_height = new_lh;
                // [claude-hwpx restate-keep-reset] 뒤 문단은 다음 쪽 맨 위 리셋(저장 위치가 앞 문단 끝보다 작아지는 자리) 전까지만 같은 양을 민다. 편집용
                // recalculate_section_vpos 는 앞 흐름이 밀리면 저장 리셋을 흐름에 이어 붙여(stale-reset-edit) 한/글 쪽 나눔 자리를
                // 지웠다(c36: 1.3px 다시 잰 표 뒤 8~10쪽이 12~52px 어긋남)
                {
                    let paras = &mut doc.document.sections[si].paragraphs;
                    let mut prev_end = old_end;
                    for q in pi + 1..paras.len() {
                        let Some(first) = paras[q].line_segs.first().map(|s| s.vertical_pos) else {
                            continue;
                        };
                        if prev_end.is_some_and(|e| first < e) {
                            break;
                        }
                        prev_end = crate::renderer::composer::paragraph_flow_end(&paras[q]);
                        for s in &mut paras[q].line_segs {
                            s.vertical_pos = s.vertical_pos.saturating_add(claude_delta);
                        }
                    }
                }
                doc.recompose_paragraph(si, pi);
