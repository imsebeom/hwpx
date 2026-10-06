// ==== find ====
                            + hwpunit_to_px(nested.outer_margin_bottom as i32, self.dpi);
                        Some(mt.total_height.max(declared) + om)
// ==== replace ====
                            + hwpunit_to_px(nested.outer_margin_bottom as i32, self.dpi);
                        // [claude-hwpx empty-host-nested-tab] 글 없는 문단 하나에 든 위아래 배치 표(글자처럼 취급 아님)는
                        // 한/글이 그 빈 줄을 표 윗자리에 겹쳐 두고 다음 문단을 표 아래에서 시작한다(한국문화 12단원 한/글
                        // 재저장: 표 문단 vpos 25447, 다음 문단 31141 = 표 5128 + 바깥 여백 566). 줄 높이 합에 이미 든 그 빈
                        // 줄을 표 높이에서 뺀다. 저장 줄 배치가 있는 문단은 종전대로 둔다
                        if !nested.common.treat_as_char
                            && matches!(nested.common.text_wrap, crate::model::shape::TextWrap::TopAndBottom)
                            && p.controls.len() == 1
                            && crate::renderer::para_has_no_stored_line_segs(p)
                            && !p.text.chars().any(|ch| ch > '\u{001F}' && ch != '\u{FFFC}' && !ch.is_whitespace())
                        {
                            let host_line = p
                                .line_segs
                                .first()
                                .map(|s| hwpunit_to_px(s.line_height + s.line_spacing.max(0), self.dpi))
                                .unwrap_or(0.0);
                            return Some((mt.total_height.max(declared) + om - host_line).max(0.0));
                        }
                        Some(mt.total_height.max(declared) + om)
