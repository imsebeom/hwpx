// ==== find ====
    /// 본문 커서 위치의 각주 마커를 조회한다.
// ==== replace ====
    /// [claude-hwpx note-renumber] 각주, 미주 번호를 문서 순서대로 다시 매긴다(붙여넣기, 범위 지우기 뒤).
    pub(crate) fn claude_renumber_notes(&mut self) {
        use crate::model::footnote::FootnoteNumbering;
        fn walk(paras: &mut [Paragraph], fn_n: &mut Option<u16>, en_n: &mut u16, depth: usize) {
            if depth > 8 {
                return;
            }
            for para in paras.iter_mut() {
                for ctrl in para.controls.iter_mut() {
                    match ctrl {
                        Control::Footnote(f) => {
                            if let Some(n) = fn_n.as_mut() {
                                f.number = *n;
                                *n += 1;
                            }
                        }
                        Control::Endnote(e) => {
                            e.number = *en_n;
                            *en_n += 1;
                        }
                        Control::Table(t) => {
                            for cell in t.cells.iter_mut() {
                                walk(&mut cell.paragraphs, fn_n, en_n, depth + 1);
                            }
                        }
                        Control::Shape(shape) => {
                            if let Some(tb) = shape.drawing_mut().and_then(|d| d.text_box.as_mut()) {
                                walk(&mut tb.paragraphs, fn_n, en_n, depth + 1);
                            }
                        }
                        _ => {}
                    }
                }
            }
        }
        let mut fn_count: u16 = 1;
        let mut en_count: u16 = 1;
        for (si, section) in self.document.sections.iter_mut().enumerate() {
            let fs = &section.section_def.footnote_shape;
            let es = &section.section_def.endnote_shape;
            if si == 0 || fs.numbering == FootnoteNumbering::RestartSection {
                fn_count = fs.start_number.max(1);
            }
            if si == 0 || es.numbering == FootnoteNumbering::RestartSection {
                en_count = es.start_number.max(1);
            }
            let mut fn_n = (fs.numbering != FootnoteNumbering::RestartPage).then_some(fn_count);
            walk(&mut section.paragraphs, &mut fn_n, &mut en_count, 0);
            if let Some(n) = fn_n {
                fn_count = n;
            }
        }
    }

    /// 본문 커서 위치의 각주 마커를 조회한다.
