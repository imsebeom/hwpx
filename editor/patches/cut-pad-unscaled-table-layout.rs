// ==== find ====
            let (_, _, pad_top, pad_bottom) = self.resolve_cell_padding(cell, table);
            max_padding = max_padding.max(pad_top + pad_bottom);
// ==== replace ====
            let (_, _, pad_top, pad_bottom) = self.resolve_cell_padding(cell, table);
            // [claude-hwpx cut-pad-unscaled] 선언 높이가 여백뿐이라 여백을 줄인 칸도 남은 내용이 선언을 넘으면 한/글은 원래 여백을 쓴다(issue1949 거대 칸)
            let (pad_top, pad_bottom) = if self.profile.get().hwpx_container() && cell.height < 0x8000_0000 {
                let decl_h = hwpunit_to_px(cell.height as i32, self.dpi);
                let (_, _, raw_top, raw_bottom) = self.claude_cell_padding_unscaled(cell, table);
                let rest: f64 = units[su..].iter().map(|unit| unit.height).sum();
                if rest > decl_h
                    && crate::model::table::Cell::vertical_padding_is_abnormal(decl_h, raw_top + raw_bottom)
                {
                    (raw_top, raw_bottom)
                } else {
                    (pad_top, pad_bottom)
                }
            } else {
                (pad_top, pad_bottom)
            };
            max_padding = max_padding.max(pad_top + pad_bottom);
