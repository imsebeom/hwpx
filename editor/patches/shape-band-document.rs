// ==== find ====
                    let is_host = section.paragraphs[hi].controls.iter().any(|c| {
                        matches!(c, Control::Picture(p)
                            if !p.common.treat_as_char
                                && p.common.text_wrap == crate::model::shape::TextWrap::Square)
                    });
// ==== replace ====
                    let is_host = section.paragraphs[hi].controls.iter().any(|c| {
                        matches!(c, Control::Picture(p)
                            if !p.common.treat_as_char
                                && p.common.text_wrap == crate::model::shape::TextWrap::Square)
                            // [claude-hwpx shape-band] 어울림 도형(차트, OLE 등)도
                            || matches!(c, Control::Shape(s)
                                if !s.common().treat_as_char
                                    && s.common().text_wrap == crate::model::shape::TextWrap::Square)
                    });
