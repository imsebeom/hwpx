// ==== find ====
                        .map(|hu| hwpunit_to_px(hu, self.dpi))
                        .unwrap_or(0.0)
                    });
// ==== replace ====
                        .map(|hu| hwpunit_to_px(hu, self.dpi))
                        // [claude-hwpx empty-float-outer-top] 저장 줄 배치가 없는 빈 문단(스킬 산출물)의 표는 한/글이 다시
                        // 조판하며 「문단 위치 + 세로 오프셋 + 바깥 위 여백」에 놓는다. #6378 은 원본 HWPX 에 위 여백을 싣지
                        // 않는데(저장 사다리 문서에서 #1133 반증), 줄 배치가 없으면 그 근거가 없어 표가 위 여백만큼 높게
                        // 그려졌다(2026-10-17 KTX 1.9px, 교과 평가계획 3.8px — 한/글 PDF 괘선 대조). 흐름은 empty-float-offset-flow
                        // 가 문단 위치 기준으로 따로 더하므로 표만 내려간다
                        .or_else(|| {
                            crate::renderer::para_has_no_stored_line_segs(para)
                                .then(|| hwpunit_to_px(t.outer_margin_top as i32, self.dpi))
                        })
                        .unwrap_or(0.0)
                    });
