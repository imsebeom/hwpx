// ==== find ====
                if let (Some(first_seg), Some(page_top_vpos)) =
                    (para.line_segs.first(), page_top_vpos_opt)
                {
// ==== replace ====
                // [claude-hwpx heading-orphan-stored] 합성 줄(엔진이 만든 줄 기록)의 vpos 는 쪽 나눔을 모르는 누적값이라 이 보정에 쓰지 않는다.
                let stored_first_seg = para
                    .line_segs
                    .first()
                    .filter(|s| s.tag & LineSeg::TAG_IMPLEMENTATION_PROPERTY == 0);
                if let (Some(first_seg), Some(page_top_vpos)) =
                    (stored_first_seg, page_top_vpos_opt)
                {
