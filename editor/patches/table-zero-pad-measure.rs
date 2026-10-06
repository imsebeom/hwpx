// ==== find ====
                } else {
                    cell.effective_padding(&table.padding)
                };
// ==== replace ====
                } else {
                    cell.effective_padding_in(table) /* [claude-hwpx table-zero-pad] */
                };
// ==== next ====
                // 행높이 측정이 갈린다 (admrul_0296 행 32.37→31.60, 표 3.87px).
                let eff_pad = cell.effective_padding(&table.padding);
                let (pad_top, pad_bottom) = (
// ==== replace ====
                // 행높이 측정이 갈린다 (admrul_0296 행 32.37→31.60, 표 3.87px).
                let eff_pad = cell.effective_padding_in(table) /* [claude-hwpx table-zero-pad] */;
                let (pad_top, pad_bottom) = (
// ==== next ====
                    // [#1809] aim 직접 분기 → 단일 출처 통일 (위 2-c단계와 동일 근거)
                    let eff_pad = cell.effective_padding(&table.padding);
                    let pad_top = hwpunit_to_px(eff_pad.top as i32, self.dpi);
// ==== replace ====
                    // [#1809] aim 직접 분기 → 단일 출처 통일 (위 2-c단계와 동일 근거)
                    let eff_pad = cell.effective_padding_in(table) /* [claude-hwpx table-zero-pad] */;
                    let pad_top = hwpunit_to_px(eff_pad.top as i32, self.dpi);
