// ==== find ====
        let fs = if lb.max_font_size > 0.0 {
            lb.max_font_size
        } else {
            12.0
        };
        let mut text_seg = make_line_seg(utf16_start, fs);
// ==== replace ====
        let fs = if lb.max_font_size > 0.0 {
            lb.max_font_size
        } else {
            12.0
        };
        // [claude-hwpx end-run-height] 마지막 줄은 문단 끝 빈 run(문단 부호의 글자 모양)의 크기도 센다
        // (정답본 1,330건 중 1,204건이 끝 run 크기, 글 run 크기는 0건. 한국문화 1단원 제목 25pt)
        let fs = if line_idx + 1 == line_breaks.len() && text_len > 0 {
            let text_end_u16 = char_index_to_utf16_offset(para, text_len);
            para.char_shapes
                .iter()
                .filter(|c| c.start_pos >= text_end_u16)
                .filter_map(|c| styles.char_styles.get(c.char_shape_id as usize))
                .map(|style| style.font_size)
                .fold(fs, f64::max)
        } else {
            fs
        };
        let mut text_seg = make_line_seg(utf16_start, fs);
