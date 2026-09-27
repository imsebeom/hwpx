// ==== find ====
                                if candidate.line_segs.len() != stored_line_count {
                                    cell_para.line_segs = candidate.line_segs;
                                } else {
                                    cell_para.line_segs = stored_line_segs;
                                }
// ==== replace ====
                                // [claude-hwpx cell-reflow-starts] 줄 수가 같아도 줄 경계가 옮겨졌으면 후보를 쓴다.
                                // 줄 수만 보면 마지막 줄이 짧은 문단에 글을 넣었을 때 입력 전 경계가 복원되어,
                                // 넣은 글이 한 줄에 몰리고 넘친 줄의 자간이 눌린다(2026-09-27 실측, 4줄 칸 문단에 29자).
                                // 저장본의 text_start 는 입력 길이만큼 이미 밀려 있으므로 그대로 비교한다.
                                let same_starts = candidate
                                    .line_segs
                                    .iter()
                                    .map(|s| s.text_start)
                                    .eq(stored_line_segs.iter().map(|s| s.text_start));
                                if candidate.line_segs.len() != stored_line_count || !same_starts {
                                    cell_para.line_segs = candidate.line_segs;
                                } else {
                                    cell_para.line_segs = stored_line_segs;
                                }
