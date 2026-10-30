// ==== find ====
                    let trigger = trigger
                        && !omit_pushed_empty_page
                        && !hangul2024_refit
// ==== replace ====
                    // [claude-hwpx block-host-reset] 위아래 배치 표가 든 문단이고 표가 남은 자리에 들어가면 쪽을 넘기지 않는다(품은 빈 줄만 다음 쪽)
                    let claude_block_host_fits = para.controls.iter().any(|c| matches!(c, Control::Table(t) if !t.common.treat_as_char
                            && t.common.text_wrap == crate::model::shape::TextWrap::TopAndBottom
                            && st.current_height + crate::renderer::hwpunit_to_px(t.common.height as i32, self.dpi)
                                <= st.available_height()));
                    let trigger = trigger
                        && !claude_block_host_fits
                        && !omit_pushed_empty_page
                        && !hangul2024_refit
