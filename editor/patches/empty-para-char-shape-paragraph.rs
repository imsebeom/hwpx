// ==== find ====
        if start_char_offset >= end_char_offset || self.char_offsets.is_empty() {
            return;
        }
        // [#4149] char_shapes 변이 — 단일줄 과밀 memo 무효화.
// ==== replace ====
        // [claude-hwpx empty-para-char-shape] 글이 하나도 없는 문단에 0..0 을 주면 그 문단의 글자 모양(문단 끝 표시)을 바꾼다.
        // 한/글은 빈 칸을 골라 글자 크기를 바꾸면 그 빈 줄 높이도 바뀐다. 종전에는 아무 일도 안 해, 표 전체 글자를 20pt 에서
        // 8pt 로 줄여도 열 추가로 생긴 빈 칸만 20pt 로 남아 행이 높았다(2026-10-25 편집 순서 시험, 한/글은 그 문서를 2쪽으로)
        if start_char_offset == 0
            && end_char_offset == 0
            && self.char_offsets.is_empty()
            && self.text.is_empty()
        {
            self.invalidate_single_line_overflow_memo();
            self.char_shapes = vec![CharShapeRef {
                start_pos: 0,
                char_shape_id: new_char_shape_id,
            }];
            return;
        }
        if start_char_offset >= end_char_offset || self.char_offsets.is_empty() {
            return;
        }
        // [#4149] char_shapes 변이 — 단일줄 과밀 memo 무효화.
