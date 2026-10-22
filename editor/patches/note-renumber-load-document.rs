// ==== find ====
        doc.rebuild_embedded_exact_font_sources();
        doc.recompose_all_with_horizontal_shaping();
        doc.paginate();
// ==== replace ====
        // [claude-hwpx note-renumber-load] 한/글은 각주, 미주의 저장 번호를 무시하고 문서 순서대로 매긴다(가이드북 파트2 합본 16번째 각주 number=1, 한/글 PDF 16)).
        // 새 번호 컨트롤이 있으면 claude_renumber_notes 가 그것을 모르므로 그대로 둔다
        fn claude_has_note_newnum(paras: &[crate::model::paragraph::Paragraph], depth: usize) -> bool {
            use crate::model::control::{AutoNumberType, Control};
            depth <= 8
                && paras.iter().any(|p| {
                    p.controls.iter().any(|c| match c {
                        Control::NewNumber(n) => {
                            matches!(n.number_type, AutoNumberType::Footnote | AutoNumberType::Endnote)
                        }
                        Control::Table(t) => t.cells.iter().any(|cell| claude_has_note_newnum(&cell.paragraphs, depth + 1)),
                        Control::Shape(s) => s
                            .drawing()
                            .and_then(|d| d.text_box.as_ref())
                            .is_some_and(|tb| claude_has_note_newnum(&tb.paragraphs, depth + 1)),
                        _ => false,
                    })
                })
        }
        if matches!(doc.source_format, crate::parser::FileFormat::Hwpx)
            && !doc.document.sections.iter().any(|s| claude_has_note_newnum(&s.paragraphs, 0))
        {
            doc.claude_renumber_notes();
        }
        doc.rebuild_embedded_exact_font_sources();
        doc.recompose_all_with_horizontal_shaping();
        doc.paginate();
