// ==== find ====
            let mut first: Vec<Option<usize>> = vec![None; doc.document.sections.len()];
// ==== replace ====
            // [claude-hwpx nolineseg-tac-line] 문서 단위 판정: 재 본 높이가 적힌 높이와 25% 넘게 다른 표가 있으면 적힌 높이가 생성기 어림값인 문서다. 줄 배치만 지운 한/글
            // 저장본은 적힌 높이가 맞으니 품은 줄을 건드리지 않는다(엔진 측정으로 바꾸면 정답본 쪽수 100 → 97.6%)
            let claude_estimated_doc = targets.iter().any(|&(si, pi, ci)| {
                let p = &doc.document.sections[si].paragraphs[pi];
                let Some(Control::Table(t)) = p.controls.get(ci) else {
                    return false;
                };
                let px = crate::renderer::height_measurer::HeightMeasurer::new(doc.dpi)
                    .measure_table_for_edit(t, pi, ci, &doc.styles);
                let (new_h, old) = (crate::renderer::px_to_hwpunit(px, doc.dpi), t.common.height as i32);
                (new_h - old).abs() * 4 > old
            });
            let mut first: Vec<Option<usize>> = vec![None; doc.document.sections.len()];
// ==== next ====
                if new_h <= 0 || (new_h - t.common.height as i32).abs() < 75 {
                    continue;
                }
                t.common.height = new_h as u32;
                doc.recompose_paragraph(si, pi);
// ==== replace ====
                if new_h <= 0 || (new_h - t.common.height as i32).abs() < 75 {
                    continue;
                }
                // [claude-hwpx nolineseg-tac-line] 글자처럼 취급 표면 열 때 만든 품은 줄(옛 표 높이 + 여백)도 고친다(c15 상자: 줄 27.5px 로 남아 쪽 나누기가 작게 셌다)
                let claude_old = t.common.height as i32;
                let claude_tac = t.common.treat_as_char;
                let claude_outer = t.outer_margin_top as i32 + t.outer_margin_bottom as i32;
                t.common.height = new_h as u32;
                if claude_tac && claude_estimated_doc {
                    if let Some(seg) = p
                        .line_segs
                        .iter_mut()
                        .find(|s| (s.line_height - (claude_old + claude_outer)).abs() <= 75)
                    {
                        let new_lh = new_h + claude_outer;
                        if seg.line_height > 0 {
                            seg.baseline_distance =
                                (seg.baseline_distance as i64 * new_lh as i64 / seg.line_height as i64) as i32;
                        }
                        seg.line_height = new_lh;
                        seg.text_height = new_lh;
                    }
                }
                doc.recompose_paragraph(si, pi);
