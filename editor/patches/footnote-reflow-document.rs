// ==== find ====
                // [claude-hwpx tac-caption-line] 표 캡션 문단도 줄 배치가 없으면 먼저 조판한다.
// ==== replace ====
                // [claude-hwpx footnote-reflow] 줄 배치 없는 각주 문단(표 칸 안 포함)도 줄을 만든다. 없으면 각주 높이를 문단당 400 HU 로 세어
                // 표와 본문이 각주 자리까지 내려와 겹친다(가이드북 2장 표 2-11)
                if include_empty {
                    fn claude_reflow_notes(
                        ctrls: &mut [Control],
                        col_width: f64,
                        styles: &ResolvedStyleSet,
                        dpi: f64,
                    ) {
                        for ctrl in ctrls.iter_mut() {
                            let notes = match ctrl {
                                Control::Footnote(f) => Some(&mut f.paragraphs),
                                Control::Endnote(e) => Some(&mut e.paragraphs),
                                Control::Table(t) => {
                                    for cell in t.cells.iter_mut() {
                                        for cp in cell.paragraphs.iter_mut() {
                                            claude_reflow_notes(&mut cp.controls, col_width, styles, dpi);
                                        }
                                    }
                                    None
                                }
                                _ => None,
                            };
                            for fp in notes.into_iter().flatten() {
                                if fp.line_segs.is_empty() {
                                    let st = styles.para_styles.get(fp.para_shape_id as usize);
                                    reflow_line_segs(fp, ParagraphBox::body_for_style(col_width, st, dpi), styles, dpi);
                                }
                            }
                        }
                    }
                    claude_reflow_notes(&mut para.controls, col_width, styles, dpi);
                }
                // [claude-hwpx tac-caption-line] 표 캡션 문단도 줄 배치가 없으면 먼저 조판한다.
