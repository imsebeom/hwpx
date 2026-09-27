// ==== find ====
        if is_treat_as_char && delta_v != 0 {
            let para_count = self.document.sections[section_idx].paragraphs.len();

            // 아래로: v_offset >= line_height이면 반복적으로 다음 문단과 교환
            while result_ppi + 1 < para_count {
                let lh = self.document.sections[section_idx].paragraphs[result_ppi]
                    .line_segs
                    .first()
                    .map(|ls| ls.line_height)
                    .unwrap_or(1000);
                if new_v < lh {
                    break;
                }
                new_v -= lh;
                self.document.sections[section_idx]
                    .paragraphs
                    .swap(result_ppi, result_ppi + 1);
                result_ppi += 1;
            }

            // 위로: v_offset < 0이면 반복적으로 이전 문단과 교환
            while new_v < 0 && result_ppi > 0 {
                let prev_lh = self.document.sections[section_idx].paragraphs[result_ppi - 1]
                    .line_segs
                    .first()
                    .map(|ls| ls.line_height)
                    .unwrap_or(1000);
                new_v += prev_lh;
                self.document.sections[section_idx]
                    .paragraphs
                    .swap(result_ppi - 1, result_ppi);
                result_ppi -= 1;
            }

            // 최종 v_offset 갱신
            if result_ppi != parent_para_idx {
// ==== replace ====
        // 글자처럼 취급 표에서 이웃 문단을 넘기지 못하고 남은 거리. 끌기가 다음 움직임에 더해 넘긴다(tac-table-move-ret)
        let mut claude_rest = 0i32;
        if is_treat_as_char {
            let para_count = self.document.sections[section_idx].paragraphs.len();
            // 이번 끌기 거리만 쓴다(이미 적혀 있던 낡은 위치 값은 무시)
            new_v = delta_v;

            // [claude-hwpx tac-table-move] 글자처럼 취급 표는 문단 흐름 안에 놓이므로 세로, 가로 위치 값을 쓰지 않는다
            // (한/글도 무시한다). 종전에는 이웃 문단 높이만큼 끌기 전까지 남은 거리를 vertical_offset 에 적어
            // (예 -45498) 표가 그만큼 옮겨 그려지며 다른 문단과 겹쳤다(2026-09-27 실측). 이웃 문단을 절반 넘게
            // 지나면 그 문단과 자리를 바꾸고, 남은 거리는 버린다.
            // 아래로: 다음 문단 높이의 절반을 넘으면 교환
            while result_ppi + 1 < para_count {
                let lh = self.document.sections[section_idx].paragraphs[result_ppi + 1]
                    .line_segs
                    .iter()
                    .map(|ls| ls.line_height + ls.line_spacing)
                    .sum::<i32>()
                    .max(1000);
                if new_v < lh / 2 {
                    break;
                }
                new_v -= lh;
                self.document.sections[section_idx]
                    .paragraphs
                    .swap(result_ppi, result_ppi + 1);
                result_ppi += 1;
            }

            // 위로: 이전 문단 높이의 절반을 넘으면 교환
            while result_ppi > 0 {
                let prev_lh = self.document.sections[section_idx].paragraphs[result_ppi - 1]
                    .line_segs
                    .iter()
                    .map(|ls| ls.line_height + ls.line_spacing)
                    .sum::<i32>()
                    .max(1000);
                if new_v > -(prev_lh / 2) {
                    break;
                }
                new_v += prev_lh;
                self.document.sections[section_idx]
                    .paragraphs
                    .swap(result_ppi - 1, result_ppi);
                result_ppi -= 1;
            }
            claude_rest = new_v;
            new_v = 0;
            {
                let tbl = self.get_table_mut(section_idx, result_ppi, control_idx)?;
                tbl.common.horizontal_offset = 0;
                patch_raw_ctrl_field(
                    &mut tbl.raw_ctrl_data,
                    common_obj_offsets::H_OFFSET,
                    &0i32.to_le_bytes(),
                );
            }

            // 최종 v_offset 갱신(항상 0)
            {
