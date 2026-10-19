// ==== find ====
                {
                    let slots = crate::document_core::helpers::caret_control_slots(para);
                    if slots.iter().any(|slot| slot.is_some()) {
// ==== replace ====
                {
                    // [claude-hwpx sel-note-text-axis] 각주, 미주는 캐럿 칸이 아니다(글자 조각 번호, 글 넣기, 문단 길이 모두 글자 축)
                    let slots = crate::document_core::helpers::claude_caret_slots_no_notes(para);
                    if slots.iter().any(|slot| slot.is_some()) {
// ==== next ====
                                        let ta = crate::document_core::helpers::logical_to_text_offset(para, a).0;
                                        let tb = crate::document_core::helpers::logical_to_text_offset(para, b).0;
// ==== replace ====
                                        // [claude-hwpx sel-note-text-axis] 글자 축 = 캐럿 위치 - 그 앞 캐럿 칸 개체 수(각주 제외)
                                        let claude_slots_before =
                                            |pos: usize| slots.iter().filter(|s| s.is_some_and(|s| s < pos)).count();
                                        let ta = a - claude_slots_before(a);
                                        let tb = b - claude_slots_before(b);
// ==== next ====
                    let slots = crate::document_core::helpers::caret_control_slots(para);
                    let mut hit_any = false;
// ==== replace ====
                    // [claude-hwpx sel-note-text-axis] 각주, 미주는 캐럿 칸이 아니다
                    let slots = crate::document_core::helpers::claude_caret_slots_no_notes(para);
                    let mut hit_any = false;
