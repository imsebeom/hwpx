// ==== find ====
                let body = if declared > 1.0 { declared } else { table_total_height };
                st.current_height += pre_height + body + hwpunit_to_px(extras_hu as i32, self.dpi);
// ==== replace ====
                let body = if declared > 1.0 { declared } else { table_total_height };
                // [claude-hwpx empty-host-caption] 선언 높이는 캡션을 품지 않는다 — 위, 아래 캡션은 캡션 간격 + 캡션 줄 높이를 더한다(한/글 재저장본, 가이드북 파트2 표 5-2)
                let claude_caption = match table.caption.as_ref() {
                    Some(cap)
                        if declared > 1.0
                            && matches!(
                                cap.direction,
                                crate::model::shape::CaptionDirection::Top
                                    | crate::model::shape::CaptionDirection::Bottom
                            ) =>
                    {
                        let h = crate::renderer::composer::caption_height_px(&table.caption, self.dpi);
                        if h > 0.0 { h + hwpunit_to_px(cap.spacing as i32, self.dpi) } else { 0.0 }
                    }
                    _ => 0.0,
                };
                st.current_height += pre_height + body + claude_caption + hwpunit_to_px(extras_hu as i32, self.dpi);
