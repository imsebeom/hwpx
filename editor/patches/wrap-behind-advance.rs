// ==== find ====
                            if matches!(
                                pic.common.text_wrap,
                                crate::model::shape::TextWrap::InFrontOfText
                            ) {
                                result_y = saved_y_offset;
                            }
// ==== replace ====
                            // [claude-hwpx wrap-behind-advance] 글 뒤로 그림도 글이 있는 문단이면 되감지 않는다. 되감으면
                            // 다음 문단이 그림 문단 윗변부터 그려져 두 문단이 겹쳤다. 빈 문단(복학원서의 로고)은 종전대로
                            let behind_on_text = matches!(
                                pic.common.text_wrap,
                                crate::model::shape::TextWrap::BehindText
                            ) && para.text.chars().any(|c| c > '\u{001F}' && c != '\u{FFFC}');
                            if behind_on_text
                                || matches!(
                                    pic.common.text_wrap,
                                    crate::model::shape::TextWrap::InFrontOfText
                                )
                            {
                                result_y = saved_y_offset;
                            }
