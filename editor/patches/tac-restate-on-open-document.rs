// ==== find ====
        doc.recompose_all_with_horizontal_shaping();
        doc.paginate();
// ==== replace ====
        doc.recompose_all_with_horizontal_shaping();
        // [claude-hwpx tac-restate-on-open] 한/글처럼 열 때 글자처럼 취급 표 높이를 행 내용으로 다시 잰다. 에디터 저장본은 옛 엔진 값이 적혀 있다
        // (결과보고서 88번 표: 적힌 15720, 한/글 15186). 표만 든 문단, 한/글이 쓴 줄(합성 줄 아님), 줄 = 선언 + 바깥 여백일 때만.
        // 글꼴 폭 준비와 전체 조판이 끝난 뒤에 재야 조판 측정과 같다
        if matches!(doc.source_format, crate::parser::FileFormat::Hwpx) {
            use crate::model::control::Control;
            let mut targets = Vec::new();
            for (si, sec) in doc.document.sections.iter().enumerate() {
                for (pi, p) in sec.paragraphs.iter().enumerate() {
                    let tacs: Vec<usize> = p
                        .controls
                        .iter()
                        .enumerate()
                        .filter(|(_, c)| matches!(c, Control::Table(t) if t.common.treat_as_char))
                        .map(|(i, _)| i)
                        .collect();
                    if tacs.len() != 1
                        || p.line_segs.len() != 1
                        || p.line_segs[0].tag & 0x8000_0000 != 0
                        || !p.text.chars().all(|c| c.is_whitespace() || c.is_control())
                    {
                        continue;
                    }
                    let Some(Control::Table(t)) = p.controls.get(tacs[0]) else {
                        continue;
                    };
                    let outer = t.outer_margin_top as i32 + t.outer_margin_bottom as i32;
                    if t.caption.is_some()
                        || (p.line_segs[0].line_height - (t.common.height as i32 + outer)).abs() > 75
                    {
                        continue;
                    }
                    targets.push((si, pi, tacs[0]));
                }
            }
            for (si, pi, ci) in targets {
                let (new_h, old_end) = {
                    let p = &doc.document.sections[si].paragraphs[pi];
                    let Some(Control::Table(t)) = p.controls.get(ci) else {
                        continue;
                    };
                    let px = crate::renderer::height_measurer::HeightMeasurer::new(doc.dpi)
                        .measure_table_for_edit(t, pi, ci, &doc.styles);
                    (crate::renderer::px_to_hwpunit(px, doc.dpi), crate::renderer::composer::paragraph_flow_end(p))
                };
                let p = &mut doc.document.sections[si].paragraphs[pi];
                let Some(Control::Table(t)) = p.controls.get_mut(ci) else {
                    continue;
                };
                let old_h = t.common.height as i32;
                if new_h <= 0 || (new_h - old_h).abs() < 75 {
                    continue;
                }
                let outer = t.outer_margin_top as i32 + t.outer_margin_bottom as i32;
                t.common.height = new_h as u32;
                let seg = &mut p.line_segs[0];
                let new_lh = new_h + outer;
                if seg.line_height > 0 {
                    seg.baseline_distance = (seg.baseline_distance as i64 * new_lh as i64 / seg.line_height as i64) as i32;
                }
                seg.line_height = new_lh;
                seg.text_height = new_lh;
                doc.claude_shift_following_vpos(si, pi, old_end);
                doc.recompose_paragraph(si, pi);
            }
        }
        doc.paginate();
