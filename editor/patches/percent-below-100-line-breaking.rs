// ==== find ====
                } else {
                    spacing.round() as i32
                }
// ==== replace ====
                } else {
                    // [claude-hwpx percent-below-100] 100% 미만도 4 단위로 반올림(0 에서 먼 쪽): 900 x -55% = -495 -> -496(정답본 수백 줄)
                    ((spacing / 4.0).round() as i32) * 4
                }
