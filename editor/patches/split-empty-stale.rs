// ==== find ====
                    cell.paragraphs
                        .iter()
                        .flat_map(|p| p.line_segs.iter())
                        .any(|ls| i64::from(ls.segment_width) > i64::from(owner_width))
// ==== replace ====
                    // [claude-hwpx split-empty-stale] 위아래로 나누면 폭이 그대로라 위 판별에 안 걸리는데, 새 칸은 원본 첫 문단의
                    // 줄 배치를 복사해 그림 줄 높이(28421)를 가진 빈 문단이 된다 — 빈 칸이 그림 칸만큼 높아졌다(2026-10-02 가이드북
                    // 그림 상자 합치기/나누기, 빈 칸 382.7px). 글도 개체도 없는 문단의 줄 높이가 100pt 를 넘으면 낡은 값으로 본다
                    cell.paragraphs
                        .iter()
                        .flat_map(|p| p.line_segs.iter())
                        .any(|ls| i64::from(ls.segment_width) > i64::from(owner_width))
                        || cell.paragraphs.iter().any(|p| {
                            p.text.is_empty()
                                && p.controls.is_empty()
                                && p.line_segs.iter().any(|ls| ls.line_height > 10000)
                        })
