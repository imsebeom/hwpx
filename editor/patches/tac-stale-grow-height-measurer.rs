// ==== find ====
        let generator_restated_height = !self.is_native_hwp5
            && table.cells.iter().all(|c| {
                c.paragraphs.iter().all(crate::renderer::para_has_no_stored_line_segs)
            });
// ==== replace ====
        let generator_restated_height = !self.is_native_hwp5
            && (table.cells.iter().all(|c| {
                c.paragraphs.iter().all(crate::renderer::para_has_no_stored_line_segs)
            })
                // [claude-hwpx tac-stale-grow] 줄 배치가 빠진 칸 문단이 든 칸의 행이 칸 선언보다 커졌으면 그 내용은 선언을 적은 뒤에 바뀐 것이다
                // (한국문화 1단원 지도 표: 한/글 364px. 그 칸이 선언 안에 들고 다른 행만 넘치면 한/글은 선언대로, 회귀 r12)
                || (table.common.treat_as_char
                    && table.cells.iter().any(|c| {
                        let r = c.row as usize;
                        c.row_span == 1
                            && r < row_heights.len()
                            && c.height < 0x8000_0000
                            && c.paragraphs.iter().any(crate::renderer::para_has_no_stored_line_segs)
                            && row_heights[r] > hwpunit_to_px(c.height as i32, self.dpi) + 0.5
                    })));
