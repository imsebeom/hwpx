// ==== find ====
                    .is_some_and(|s| s.tag & crate::model::paragraph::LineSeg::TAG_IMPLEMENTATION_PROPERTY == 0);
            if (was_tac
// ==== replace ====
                    .is_some_and(|s| {
                        // [claude-hwpx keep-synth-shape] 엔진이 만든 줄도 도형 항목 뒤에는 둔다(d334, d034). 표 항목 뒤는 앞 문단 아래 간격이 빠져 버린다(d167)
                        s.tag & crate::model::paragraph::LineSeg::TAG_IMPLEMENTATION_PROPERTY == 0
                            || matches!(item, PageItem::Shape { .. })
                    });
            if (was_tac
