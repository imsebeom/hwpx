// ==== find ====
                                        let ta = crate::document_core::helpers::logical_to_text_offset(para, a).0;
                                        let tb = crate::document_core::helpers::logical_to_text_offset(para, b).0;
// ==== replace ====
                                        // [claude-hwpx sel-footnote-slot] 렌더 조각 번호는 각주, 미주 번호 자리를 한 칸으로 센다 — 글자 축으로 바꾼 뒤 앞선 각주, 미주 수를 더한다
                                        let claude_notes_before = |pos: usize| {
                                            slots
                                                .iter()
                                                .enumerate()
                                                .filter(|(ci, slot)| {
                                                    slot.is_some_and(|s| s < pos)
                                                        && matches!(
                                                            para.controls.get(*ci),
                                                            Some(crate::model::control::Control::Footnote(_))
                                                                | Some(crate::model::control::Control::Endnote(_))
                                                        )
                                                })
                                                .count()
                                        };
                                        let ta = crate::document_core::helpers::logical_to_text_offset(para, a).0 + claude_notes_before(a);
                                        let tb = crate::document_core::helpers::logical_to_text_offset(para, b).0 + claude_notes_before(b);
