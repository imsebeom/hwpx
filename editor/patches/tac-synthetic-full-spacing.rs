// ==== find ====
                        let current_owned_row_covers_object =
                            self.profile.get().hwpx_stored_layout()
                                && para.line_segs.len() == 1
// ==== replace ====
                        // [claude-hwpx tac-synthetic-full-spacing] 줄 배치 없는 문단(스킬 산출물)의 글자처럼 취급 표 줄은 한/글이
                        // 「줄 높이(표 + 바깥 여백 위아래) + 줄 간격 전부」로 다음 문단을 놓는다(2026-10-17 교과 평가계획 한/글
                        // 재저장본: p23 줄 24158 = 23592 + 283×2, 다음 문단 vpos 24758 = 24158 + 600). 계산한 줄에 줄 간격의
                        // 절반만 더하는 아래 규칙은 이 문단에서 표마다 4px 씩 모자라게 해 끈다
                        let current_owned_row_covers_object = !crate::renderer::para_has_no_stored_line_segs(para)
                            && self.profile.get().hwpx_stored_layout()
                                && para.line_segs.len() == 1
