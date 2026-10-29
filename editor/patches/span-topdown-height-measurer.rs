// ==== find ====
        // 2-b단계: 병합 셀에서 미지 행 높이를 반복적으로 해결
// ==== replace ====
        // [claude-hwpx span-topdown] 한 행 칸으로 정한 행 높이(위에서부터 다시 풀 때 바닥)
        let claude_h1 = row_heights.clone();
        // 2-b단계: 병합 셀에서 미지 행 높이를 반복적으로 해결
// ==== next ====
        // 2-c단계: 병합 셀의 실제 컨텐츠 높이가 결합 행 높이 초과 시 마지막 행 확장
        for cell in &table.cells {
// ==== replace ====
        // 2-c단계: 병합 셀의 실제 컨텐츠 높이가 결합 행 높이 초과 시 마지막 행 확장
        // [claude-hwpx span-topdown] 병합 칸마다 (시작 행, 걸친 행 수, 내용과 선언 중 큰 값)
        let mut claude_span_req: Vec<(usize, usize, f64)> = Vec::new();
        for cell in &table.cells {
// ==== next ====
                let combined: f64 = (r..r + span).map(|i| row_heights[i]).sum();
                if required_height > combined {
                    let deficit = required_height - combined;
                    row_heights[r + span - 1] += deficit;
                }
            }
        }

        // [claude-hwpx span-ladder-trust] 미뤄 둔
// ==== replace ====
                // [claude-hwpx span-topdown]
                let claude_decl = if cell.height < 0x8000_0000 { hwpunit_to_px(cell.height as i32, self.dpi) } else { 0.0 };
                claude_span_req.push((r, span, required_height.max(claude_decl)));
                let combined: f64 = (r..r + span).map(|i| row_heights[i]).sum();
                if required_height > combined {
                    let deficit = required_height - combined;
                    row_heights[r + span - 1] += deficit;
                }
            }
        }

        // [claude-hwpx span-ladder-trust] 미뤄 둔
// ==== next ====
        // 3단계: 높이가 0인 행은 기본값 적용
// ==== replace ====
        // [claude-hwpx span-topdown] HWPX 글자처럼 취급 표에 한 행 칸 없는 행이 있으면 위에서부터 차례로 정한다 — 행마다 한 행 칸 높이와 그 행에서 끝나는
        // 병합 칸의 모자란 몫 중 큰 값. 2-b 가 내용보다 작은 병합 칸 선언으로 빈 행을 먼저 정해 부족분이 뒤 행에 쌓였다
        // (결과보고서 163번 표 10행: 엔진 29.5px, 한/글 21.7px = 8~10행 칸 선언 - 8행 - 9행, 11행 글이 4px 아래)
        if !self.is_native_hwp5 && !self.is_hwp3_variant && table.common.treat_as_char {
            let claude_fixed: Vec<bool> = (0..row_count)
                .map(|r| table.cells.iter().any(|c| c.row as usize == r && c.row_span == 1))
                .collect();
            if claude_fixed.iter().any(|f| !f) {
                let shrink = table.rowspan_declared_overflow_shrink();
                let mut h = vec![0.0f64; row_count];
                for r in 0..row_count {
                    let mut v = if claude_fixed[r] {
                        let s = shrink.get(r).copied().unwrap_or(0);
                        if s > 0 {
                            (claude_h1[r] - hwpunit_to_px(s as i32, self.dpi)).max(content_row_floor[r])
                        } else {
                            claude_h1[r]
                        }
                    } else {
                        0.0
                    };
                    for &(sr, span, req) in &claude_span_req {
                        if sr + span - 1 == r {
                            let before: f64 = h[sr..r].iter().sum();
                            v = v.max(req - before);
                        }
                    }
                    h[r] = v;
                }
                row_heights[..row_count].copy_from_slice(&h);
            }
        }
        // 3단계: 높이가 0인 행은 기본값 적용
