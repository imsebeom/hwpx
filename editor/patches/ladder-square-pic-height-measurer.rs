// ==== find ====
                            if common.treat_as_char
                                || !matches!(common.text_wrap, TextWrap::TopAndBottom)
                                || !matches!(common.vert_rel_to, VertRelTo::Para)
// ==== replace ====
                            // [claude-hwpx ladder-square-pic] 어울림 그림, 도형도 칸을 그 바닥까지 키운다(c41 15번 표: 한/글 13948 = 그림 바닥 13666 + 여백)
                            let claude_wrap_ok = matches!(common.text_wrap, TextWrap::TopAndBottom)
                                || (matches!(common.text_wrap, TextWrap::Square) && !matches!(ctl, Control::Table(_)));
                            if common.treat_as_char
                                || !claude_wrap_ok
                                || !matches!(common.vert_rel_to, VertRelTo::Para)
