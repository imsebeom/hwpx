// ==== find ====
        let raw_table_height: f64 =
            row_heights.iter().sum::<f64>() + cell_spacing * (row_count.saturating_sub(1) as f64);
// ==== replace ====
        // [claude-hwpx tac-row-ladder] 글자처럼 취급 표는 칸마다 「줄 배치 마지막 줄 끝 + 위아래 칸 여백」과 적힌 칸 높이 중
        // 큰 값으로 행 높이를 정한다(한글이 저장한 행 높이와 같다). rhwp 의 칸 내용 측정은 줄 간격, 문단 간격을 한글보다 크게
        // 잡아(d05 p4: 한글 51.2/112.2, rhwp 58.4/121.1) 평소에는 비례 축소가 가려 주다가, 칸에 문단을 더하면 축소 조건을 벗어나
        // 표가 16px 커졌다(2026-09-28). 합친 칸, 세로쓰기, 줄 배치 없는 문단이 있으면 종전 측정을 쓴다.
        if table.common.treat_as_char
            && table.cells.iter().all(|c| {
                c.row_span == 1
                    && c.text_direction == 0
                    && (c.row as usize) < row_count
                    && !c.paragraphs.is_empty()
                    && c.paragraphs.iter().all(|p| !p.line_segs.is_empty())
            })
        {
            let mut ladder = vec![0.0f64; row_count];
            for c in &table.cells {
                // 줄을 차례로 쌓아 끝을 잰다 — 줄의 위치가 앞 줄 끝 + 줄 간격보다 위면 그 자리로 내린다. 칸에 그림을 바꿔 넣은 뒤
                // 저장된 파일은 그림 뒤 빈 문단의 vertpos 가 옛 값(1600)으로 남아, 최댓값만 보면 그 줄이 칸에서 빠졌다(2026-10-02
                // 가이드북 3절 그림 3-2 상자, 한/글 441.9px 대 rhwp 421.1px). 저장 위치가 맞는 칸은 값이 그대로다
                let end = {
                    let (mut next_top, mut end) = (0i32, 0i32);
                    for s in c.paragraphs.iter().flat_map(|p| p.line_segs.iter()) {
                        let top = s.vertical_pos.max(next_top);
                        end = end.max(top.saturating_add(s.line_height));
                        next_top = top.saturating_add(s.line_height).saturating_add(s.line_spacing.max(0));
                    }
                    end
                };
                let pad = if c.apply_inner_margin { &c.padding } else { &table.padding };
                let need = end + pad.top as i32 + pad.bottom as i32;
                let declared = if c.height < 0x8000_0000 { c.height as i32 } else { 0 };
                let r = c.row as usize;
                ladder[r] = ladder[r].max(hwpunit_to_px(need.max(declared), self.dpi));
            }
            if ladder.iter().all(|h| *h > 0.0) {
                row_heights[..row_count].copy_from_slice(&ladder);
            }
        }
        let raw_table_height: f64 =
            row_heights.iter().sum::<f64>() + cell_spacing * (row_count.saturating_sub(1) as f64);
