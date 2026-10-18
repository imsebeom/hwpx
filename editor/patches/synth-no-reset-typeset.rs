// ==== find ====
                            || near_page_top_reset
                            || native_near_top_reset
                            || stored_top_collision_reset
                    };
// ==== replace ====
                            || near_page_top_reset
                            || native_near_top_reset
                            || stored_top_collision_reset
                    };
                    // [claude-hwpx synth-no-reset] 엔진이 만든 줄의 vpos 는 저장 쪽 경계가 아니다. 편집 도구가 줄을 다시 만들면 첫 vpos 가 0 이 되어
                    // 여기서 쪽이 끊겼다(2026-10-18 「에디터가 고치면 쪽이 어긋난다」, editor/tests/edit_consistency.mjs format_text)
                    let trigger = trigger && !para.line_segs.first().is_some_and(is_synthetic_line_seg);
