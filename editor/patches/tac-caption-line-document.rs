// ==== find ====
                // 본문 NO_LS 텍스트 문단의 실폭 래핑은 composer recompose 가 담당한다.
                if Self::needs_line_seg_reflow_in_scope(para, include_empty, section_sized) {
// ==== replace ====
                // 본문 NO_LS 텍스트 문단의 실폭 래핑은 composer recompose 가 담당한다.
                // [claude-hwpx tac-caption-line] 표 캡션 문단도 줄 배치가 없으면 먼저 조판한다. 글자처럼 취급 표의 줄 높이가
                // 캡션 높이를 쓰는데, 줄 배치 없는 캡션은 기본 400 으로 잡혀 한/글(10pt 캡션 1000)보다 낮았다(d242)
                for ctrl in para.controls.iter_mut() {
                    if let Control::Table(t) = ctrl {
                        let cap_w = crate::renderer::hwpunit_to_px(t.common.width as i32, dpi);
                        if let Some(cap) = t.caption.as_mut() {
                            for cp in cap.paragraphs.iter_mut() {
                                if Self::needs_line_seg_reflow_in_scope(cp, include_empty, section_sized) {
                                    reflow_line_segs(cp, ParagraphBox::content_width_px(cap_w, dpi), styles, dpi);
                                }
                            }
                        }
                    }
                }
                if Self::needs_line_seg_reflow_in_scope(para, include_empty, section_sized) {
