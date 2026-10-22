// ==== find ====
                // zone 영역의 좌표 계산
                let sc = zone.start_col as usize;
                let ec = (zone.end_col as usize + 1).min(col_count);
                let sr = zone.start_row as usize;
                let er = (zone.end_row as usize + 1).min(row_count);
// ==== replace ====
                // zone 영역의 좌표 계산
                // [claude-hwpx cellzone-span] 끝 주소는 칸 주소다. 끝 칸이 병합 칸이면 그 범위 끝까지 칠하고,
                // 끝 주소가 가려진 칸이면 한/글처럼 셀 영역을 쓰지 않는다(d130 사본 실험).
                let Some(end_cell) = table.cells.iter().find(|c| {
                    c.row == zone.end_row && c.col == zone.end_col
                }) else {
                    continue;
                };
                let sc = zone.start_col as usize;
                let ec = (end_cell.col as usize + (end_cell.col_span as usize).max(1)).min(col_count);
                let sr = zone.start_row as usize;
                let er = (end_cell.row as usize + (end_cell.row_span as usize).max(1)).min(row_count);
