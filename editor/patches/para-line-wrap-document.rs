// ==== find ====
        if line_wrap != crate::model::table::CELL_LINE_WRAP_SQUEEZE || para.line_segs.len() < 2 {
            return;
        }
// ==== replace ====
        // [claude-hwpx para-line-wrap] 칸의 lineWrap 이 BREAK 여도 문단 모양이 「한 줄로 입력」이면 한/글은 한 줄에 넣는다
        // (정답본 818문단 중 812개 한 줄, 나머지는 강제 줄바꿈).
        let para_squeeze = styles
            .para_styles
            .get(para.para_shape_id as usize)
            .is_some_and(|s| s.line_wrap_squeeze);
        if (line_wrap != crate::model::table::CELL_LINE_WRAP_SQUEEZE && !para_squeeze)
            || para.line_segs.len() < 2
        {
            return;
        }
// ==== next ====
                        ParagraphBox::body_for_style(col_width, para_style, dpi),
                        styles,
                        dpi,
                    );
                    body_line_seg_changed = true;
// ==== replace ====
                        ParagraphBox::body_for_style(col_width, para_style, dpi),
                        styles,
                        dpi,
                    );
                    // 본문 문단도 문단 모양이 「한 줄로 입력」이면 한 줄로(칸 lineWrap 은 없으므로 BREAK)
                    Self::claude_squeeze_one_line(para, 0, col_width, styles, dpi);
                    body_line_seg_changed = true;
// ==== next ====
                        ParagraphBox::body_for_style(col_width, para_style, dpi),
                        &styles,
                        dpi,
                    );
                    reflowed += 1;
// ==== replace ====
                        ParagraphBox::body_for_style(col_width, para_style, dpi),
                        &styles,
                        dpi,
                    );
                    Self::claude_squeeze_one_line(para, 0, col_width, &styles, dpi);
                    reflowed += 1;
