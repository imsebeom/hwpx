// ==== find ====
                doc.claude_shift_following_vpos(si, pi, old_end);
                doc.recompose_paragraph(si, pi);
            }
        }
        doc.paginate();
// ==== replace ====
                doc.claude_shift_following_vpos(si, pi, old_end);
                doc.recompose_paragraph(si, pi);
            }
        }
        // [claude-hwpx nolineseg-table-restate] 줄 배치가 하나도 없는 HWPX 표(칸 문단과 표를 품은 문단 모두)는 적힌 sz 높이가 생성기 어림값이다 — 한/글처럼
        // 열 때 칸 내용으로 다시 잰다(운영현황 1번 표: 적힌 649.6px, 내용 337.9px. 엔진은 행은 내용대로 그리고 쪽 흐름은 적힌 높이로 잡아
        // 표 뒤가 비거나 다음 표와 겹쳤다). 한/글 저장본은 줄 배치가 있어 대상이 아니다
        if matches!(doc.source_format, crate::parser::FileFormat::Hwpx) {
            use crate::model::control::Control;
            let mut targets = Vec::new();
            for (si, sec) in doc.document.sections.iter().enumerate() {
                for (pi, p) in sec.paragraphs.iter().enumerate() {
                    if !crate::renderer::para_has_no_stored_line_segs(p) {
                        continue;
                    }
                    for (ci, c) in p.controls.iter().enumerate() {
                        if let Control::Table(t) = c {
                            if t.caption.is_none()
                                && !t.cells.is_empty()
                                && t.cells.iter().all(|cell| {
                                    cell.paragraphs.iter().all(crate::renderer::para_has_no_stored_line_segs)
                                })
                            {
                                targets.push((si, pi, ci));
                            }
                        }
                    }
                }
            }
            let mut first: Vec<Option<usize>> = vec![None; doc.document.sections.len()];
            for (si, pi, ci) in targets {
                let new_h = {
                    let p = &doc.document.sections[si].paragraphs[pi];
                    let Some(Control::Table(t)) = p.controls.get(ci) else {
                        continue;
                    };
                    let px = crate::renderer::height_measurer::HeightMeasurer::new(doc.dpi)
                        .measure_table_for_edit(t, pi, ci, &doc.styles);
                    crate::renderer::px_to_hwpunit(px, doc.dpi)
                };
                let p = &mut doc.document.sections[si].paragraphs[pi];
                let Some(Control::Table(t)) = p.controls.get_mut(ci) else {
                    continue;
                };
                if new_h <= 0 || (new_h - t.common.height as i32).abs() < 75 {
                    continue;
                }
                t.common.height = new_h as u32;
                doc.recompose_paragraph(si, pi);
                first[si] = Some(first[si].map_or(pi, |f| f.min(pi)));
            }
            for (si, f) in first.into_iter().enumerate() {
                if let Some(pi) = f {
                    doc.claude_shift_following_vpos(si, pi, None);
                }
            }
        }
        doc.paginate();
