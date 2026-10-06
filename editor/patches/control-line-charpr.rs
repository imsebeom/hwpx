// ==== find ====
            {
                let mut seg = make_line_seg(start_pos, 0.0);
                if let Some(template) = orig_line_segs
// ==== replace ====
            {
                // [claude-hwpx control-line-charpr] 글 없이 글자처럼 취급 개체만 있는 줄도 한/글은 그 자리 글자 모양의
                // 크기로 줄 간격을 셈한다(한국문화 12단원 그림 칸: 10pt 160% → 한/글 재저장 600, 종전 12px 기본값 540)
                let control_font_size = para
                    .char_shapes
                    .iter()
                    .rev()
                    .find(|c| c.start_pos <= start_pos)
                    .or_else(|| para.char_shapes.first())
                    .and_then(|c| styles.char_styles.get(c.char_shape_id as usize))
                    .map(|style| style.font_size)
                    .unwrap_or(0.0);
                let mut seg = make_line_seg(start_pos, control_font_size);
                if let Some(template) = orig_line_segs
