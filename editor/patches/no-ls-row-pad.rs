// ==== find ====
                    } else {
                        line_based + pad_top + pad_bottom
                    };
// ==== replace ====
                    } else {
                        // [claude-hwpx no-ls-row-pad] 칸 선언 높이가 여백뿐이라(282 = 141 + 141) 여백을 줄여 그리는 칸도, 내용이
                        // 선언을 넘으면 한/글은 줄 + 원래 여백으로 행을 키운다(측정기 #5751 과 같은 규칙. 한국문화 12단원 칸 속 표:
                        // 한/글 행 17.1px = 13.3 + 1.9 x 2, 종전 그리기 15.2px 로 표가 측정보다 7.5px 짧고 바깥 칸 밑선에 닿았다)
                        let decl_h = if cell.height < 0x8000_0000 {
                            hwpunit_to_px(cell.height as i32, self.dpi)
                        } else {
                            0.0
                        };
                        let (_, _, raw_top, raw_bottom) = self.claude_cell_padding_unscaled(cell, table);
                        if line_based > decl_h
                            && crate::model::table::Cell::vertical_padding_is_abnormal(
                                decl_h,
                                raw_top + raw_bottom,
                            )
                        {
                            line_based + raw_top + raw_bottom
                        } else {
                            line_based + pad_top + pad_bottom
                        }
                    };
// ==== next ====
    ) -> (f64, f64, f64, f64) {
        // HWP 스펙: aim(apply_inner_margin)=true → cell.padding,
// ==== replace ====
    ) -> (f64, f64, f64, f64) {
        let (pad_left, pad_right, pad_top, pad_bottom) =
            self.claude_cell_padding_unscaled(cell, table);
        // [Task #501] 한컴 방어 로직 모방 — cell.padding.top + bottom 합산이
        // cell.height 자체를 초과하면 (mel-001 p2 셀[21]: pad=1700 HU 두 축, h=1280 HU)
        // 한컴은 자체 가드로 cell 안에 콘텐츠가 들어가도록 처리. cell.height 의 절반까지
        // 비례 축소 (HWP 스펙 외 한컴 동작 모방).
        // 발동 기준은 측정(height_measurer)과 공유한다 (#5751).
        let (pad_top, pad_bottom) = if cell.height < 0x80000000 {
            let cell_h_px = hwpunit_to_px(cell.height as i32, self.dpi);
            let total_v_pad = pad_top + pad_bottom;
            if crate::model::table::Cell::vertical_padding_is_abnormal(cell_h_px, total_v_pad) {
                let max_v_pad = cell_h_px * 0.5;
                let scale = max_v_pad / total_v_pad;
                (pad_top * scale, pad_bottom * scale)
            } else {
                (pad_top, pad_bottom)
            }
        } else {
            (pad_top, pad_bottom)
        };
        (pad_left, pad_right, pad_top, pad_bottom)
    }

    /// [claude-hwpx no-ls-row-pad] 위 비례 축소(Task #501)를 하기 전의 칸 안 여백.
    fn claude_cell_padding_unscaled(
        &self,
        cell: &crate::model::table::Cell,
        table: &crate::model::table::Table,
    ) -> (f64, f64, f64, f64) {
        // HWP 스펙: aim(apply_inner_margin)=true → cell.padding,
// ==== next ====
            hwpunit_to_px(table.padding.bottom as i32, self.dpi)
        };
        // [Task #501] 한컴 방어 로직 모방 — cell.padding.top + bottom 합산이
        // cell.height 자체를 초과하면 (mel-001 p2 셀[21]: pad=1700 HU 두 축, h=1280 HU)
        // 한컴은 자체 가드로 cell 안에 콘텐츠가 들어가도록 처리. cell.height 의 절반까지
        // 비례 축소 (HWP 스펙 외 한컴 동작 모방).
        // 발동 기준은 측정(height_measurer)과 공유한다 (#5751).
        let (pad_top, pad_bottom) = if cell.height < 0x80000000 {
            let cell_h_px = hwpunit_to_px(cell.height as i32, self.dpi);
            let total_v_pad = pad_top + pad_bottom;
            if crate::model::table::Cell::vertical_padding_is_abnormal(cell_h_px, total_v_pad) {
                let max_v_pad = cell_h_px * 0.5;
                let scale = max_v_pad / total_v_pad;
                (pad_top * scale, pad_bottom * scale)
            } else {
                (pad_top, pad_bottom)
            }
        } else {
            (pad_top, pad_bottom)
        };
// ==== replace ====
            hwpunit_to_px(table.padding.bottom as i32, self.dpi)
        };
