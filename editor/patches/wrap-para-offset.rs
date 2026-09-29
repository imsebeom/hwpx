// ==== find ====
                            let pic_y = if matches!(
                                pic.common.text_wrap,
                                crate::model::shape::TextWrap::Square
                            ) && matches!(
                                pic.common.vert_rel_to,
                                crate::model::shape::VertRelTo::Para
                            ) {
// ==== replace ====
                            // [claude-hwpx wrap-para-offset] 「좁아진 첫 줄」 추정은 그림 윗변 자체를 준다. 세로 거리가 있는
                            // 그림에 쓰면 layout_body_picture 가 거리를 한 번 더 더해 그림이 그만큼 아래로 내려갔다
                            // (문단 기준 15mm 그림이 한글보다 약 60px 아래). 거리가 있으면 문단 윗변 + 거리로 둔다
                            let pic_y = if matches!(
                                pic.common.text_wrap,
                                crate::model::shape::TextWrap::Square
                            ) && matches!(
                                pic.common.vert_rel_to,
                                crate::model::shape::VertRelTo::Para
                            ) && pic.common.vertical_offset == 0
                            {
