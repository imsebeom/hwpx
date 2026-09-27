// ==== find ====
                } else {
                    utf16_pos_to_char_idx(char_offsets, ls.text_start)
                }
// ==== replace ====
                } else {
                    // [claude-hwpx caret-axis] 줄 시작을 캐럿 축으로 — 글자 축이면 글자처럼 취급 개체가
                    // 있는 문단에서 줄 경계가 한 칸씩 밀리고, 개체 줄과 다음 줄의 시작이 같아진다.
                    crate::document_core::helpers::utf16_pos_to_caret_idx(para, ls.text_start)
                }
