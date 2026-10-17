// ==== find ====
                    let char_widths = if has_inline_control_in_range(inline_controls, start, i) {
                        (start..i)
                            .map(|ci| {
                                measure_char_width(
                                    text_chars[ci],
                                    ci,
                                    char_offsets,
                                    char_shapes,
                                    styles,
                                    current_lang,
                                    inline_controls,
                                )
                            })
                            .collect()
                    } else {
                        Vec::new()
                    };
// ==== replace ====
                    // [claude-hwpx hangul-word-char-widths] 어절이 줄보다 길어 글자 단위로 나눌 때(fill_one_interval 의 fallback)
                    // 글자별 폭이 비어 있으면 「글자 크기와 12px 중 큰 값」으로 어림해, 작은 글자나 장평, 자간을 줄인 글자가 실제보다
                    // 넓게 잡혔다. 줄 배치 없는 문서(스킬 산출물)의 좁은 칸 「노력요함」(8pt, 장평 90%, 자간 -15%, 칸 안 폭 1471)이
                    // 한 글자에 900 으로 잡혀 「노/력/요/함」 네 줄이 되고 행이 커졌다(2026-10-17 교과 평가계획 6쪽, 한/글은
                    // 「노력/요함」). 인라인 개체가 없어도 늘 실제 폭을 잰다
                    let char_widths: Vec<f64> = (start..i)
                        .map(|ci| {
                            measure_char_width(
                                text_chars[ci],
                                ci,
                                char_offsets,
                                char_shapes,
                                styles,
                                current_lang,
                                inline_controls,
                            )
                        })
                        .collect();
