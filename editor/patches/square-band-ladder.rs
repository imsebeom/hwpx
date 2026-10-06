// ==== find ====
                                )
                        }) && paragraphs
                            .get(*para_index + 1)
                            .is_some_and(para_has_visible_text);
                        let has_ladder_float = has_overlay_float || has_square_float_before_text;
// ==== replace ====
                                )
                        }) && paragraphs.get(*para_index + 1).is_some_and(|next| {
                            para_has_visible_text(next)
                                // [claude-hwpx square-band-ladder] 다음 문단이 빈 문단이어도 앵커와 같은 그림 옆 띠 줄을
                                // 한/글이 저장해 두었으면(둘 다 합성 아님, 같은 시작 위치와 폭, 단 왼쪽보다 안쪽) 그 사다리가
                                // 증언이다 — 한국문화 14단원 한/글 저장본: 그림 문단 39659, 빈 문단 41579 (모두 horzpos 34627,
                                // 폭 13561). 종전에는 증언을 묻지 않아 앵커 줄 1920 이 빠지고 아래 표가 한 줄 위에 그려졌다.
                                // 그림만 — OLE 같은 도형은 개체 항목이 그 줄을 이미 전진한다(issue_2069 Enter 시험: 두 줄이 됐다)
                                || {
                                    let synth = crate::model::paragraph::LineSeg::TAG_IMPLEMENTATION_PROPERTY;
                                    let square_picture = para.controls.iter().any(|c| {
                                        matches!(c, Control::Picture(pic)
                                            if !pic.common.treat_as_char
                                                && matches!(pic.common.text_wrap, TextWrap::Square))
                                    });
                                    square_picture && match (para.line_segs.as_slice(), next.line_segs.first()) {
                                        ([host], Some(n)) => {
                                            host.tag & synth == 0
                                                && n.tag & synth == 0
                                                && host.column_start > 0
                                                && host.column_start == n.column_start
                                                && host.segment_width == n.segment_width
                                        }
                                        _ => false,
                                    }
                                }
                        });
                        let has_ladder_float = has_overlay_float || has_square_float_before_text;
