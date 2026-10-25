// ==== find ====
            para.line_segs.clear();
            reflow_line_segs(para, paragraph_box, &styles, dpi);
        }
        // [claude-hwpx edit-vpos-chain]
// ==== replace ====
            para.line_segs.clear();
            reflow_line_segs(para, paragraph_box, &styles, dpi);
            // [claude-hwpx reflow-notes] 각주, 미주 글도 본문 폭으로 접히므로 함께 다시 접는다(칸 안 글에 단 각주도 쪽 아래 각주
            // 영역에 놓여 본문 폭을 따른다). 종전에는 옛 폭의 줄 나눔이 남아 좌우 여백을 넓히면 각주가 줄 수가 적은 채로 남고,
            // 그만큼 본문이 한 쪽에 더 들어갔다(2026-10-25 편집 순서 시험: 3장 원고 좌우 40mm 에서 1쪽에 한 줄 더, 한/글과
            // 처음부터 조판한 결과는 각주를 새 폭으로 접어 다음 쪽으로)
            fn reflow_notes_in(
                para: &mut crate::model::paragraph::Paragraph,
                wrap_width: f64,
                styles: &ResolvedStyleSet,
                dpi: f64,
            ) {
                for ctrl in para.controls.iter_mut() {
                    let notes = match ctrl {
                        crate::model::control::Control::Footnote(f) => &mut f.paragraphs,
                        crate::model::control::Control::Endnote(e) => &mut e.paragraphs,
                        crate::model::control::Control::Table(t) => {
                            for cell in t.cells.iter_mut() {
                                for p in cell.paragraphs.iter_mut() {
                                    reflow_notes_in(p, wrap_width, styles, dpi);
                                }
                            }
                            continue;
                        }
                        _ => continue,
                    };
                    for note in notes.iter_mut() {
                        let note_box = ParagraphBox::body_for_style(
                            wrap_width,
                            styles.para_styles.get(note.para_shape_id as usize),
                            dpi,
                        );
                        note.line_segs.clear();
                        reflow_line_segs(note, note_box, styles, dpi);
                    }
                    claude_rechain_vpos(notes, styles, dpi);
                }
            }
            reflow_notes_in(para, wrap_width, &styles, dpi);
        }
        // [claude-hwpx edit-vpos-chain]
