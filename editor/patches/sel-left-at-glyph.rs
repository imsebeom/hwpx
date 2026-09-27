// ==== find ====
                    let (page_idx, rect_x, rect_y, rect_h) =
                        if !partial_start && cell_target.is_none() {
                            (lh.page, area_left, lh.y, lh.h)
                        } else {
                            (lh.page, lh.x, lh.y, lh.h)
                        };
// ==== replace ====
                    // [claude-hwpx sel-left-at-glyph] 줄 첫 글자부터 고르면 음영이 단 왼쪽 끝(area_left)에서 시작해
                    // 가운데, 오른쪽 정렬 문단의 빈 여백까지 칠해졌다. 셀 안처럼 언제나 첫 글자 자리(lh.x)에서 시작한다.
                    let _ = area_left;
                    let (page_idx, rect_x, rect_y, rect_h) = (lh.page, lh.x, lh.y, lh.h);
