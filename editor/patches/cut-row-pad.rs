// ==== find ====
                    + mixed_nested_extra;
            let (_, _, pad_top, pad_bottom) = self.resolve_cell_padding(cell, table);
// ==== replace ====
                    + mixed_nested_extra;
            // [claude-hwpx cut-row-pad] 칸 선언 높이가 여백뿐이라(566 = 283 + 283) 여백을 줄여 쓰는 칸도, 내용이 선언을 넘으면
            // 한/글은 원래 여백으로 행을 키운다(no-ls-row-pad 와 같은 규칙의 쪽에 걸친 행 판). 2026-10-17 교과 평가계획 8쪽: 잘린
            // 「노력요함」 행의 나머지가 한/글 48.0px = 내용 40.5 + 3.8 x 2 인데 rhwp 는 여백을 1.9 로 줄여 44.3px
            let (_, _, pad_top, pad_bottom) = {
                let (l, r, t, b) = self.resolve_cell_padding(cell, table);
                let decl_h = if cell.height < 0x8000_0000 {
                    hwpunit_to_px(cell.height as i32, self.dpi)
                } else {
                    0.0
                };
                let (_, _, raw_top, raw_bottom) = self.claude_cell_padding_unscaled(cell, table);
                // 저장 줄 배치가 있는 칸은 종전대로 — 이 값은 쪽 나누기에도 쓰여 저장 문서의 나눔을 바꾼다(#3820 p106 표 29,
                // issue1949 큰 칸 시험이 깨졌다)
                if content > decl_h
                    && cell
                        .paragraphs
                        .iter()
                        .all(crate::renderer::para_has_no_stored_line_segs)
                    && crate::model::table::Cell::vertical_padding_is_abnormal(
                        decl_h,
                        raw_top + raw_bottom,
                    )
                {
                    (l, r, raw_top, raw_bottom)
                } else {
                    (l, r, t, b)
                }
            };
