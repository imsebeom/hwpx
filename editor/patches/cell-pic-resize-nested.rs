// ==== find ====
        if claude_before.is_some() {
            let (tci, ci, cpi) = path[0];
            self.reflow_cell_paragraph(section_idx, parent_para_idx, tci, ci, cpi);
            if claude_restored {
                self.recalculate_cell_paragraph_vpos_native(section_idx, parent_para_idx, tci, ci, 0, None);
            }
        }

        self.recompose_section(section_idx);
// ==== replace ====
        if claude_before.is_some() {
            let (tci, ci, cpi) = path[0];
            self.reflow_cell_paragraph(section_idx, parent_para_idx, tci, ci, cpi);
            if claude_restored {
                self.recalculate_cell_paragraph_vpos_native(section_idx, parent_para_idx, tci, ci, 0, None);
            }
        }
        // [claude-hwpx cell-pic-resize-nested] 표 속 표 칸의 그림 크기를 바꾸면 그 칸 문단의 줄을 새 그림 높이로 다시 나누고
        // 뒤 문단의 세로 위치를 다시 매긴 뒤, 안쪽 표부터 높이를 다시 잰다(tac-nested-sync). 종전에는 1단 칸에만 보정이 있어
        // 표 속 표에서는 그림만 작아지고 상자 높이와 다음 문단이 그대로였다(2026-10-06 사용자 보고 「표 속의 이미지 크기 줄였을 때
        // 표의 크기 자동 조절이나 다음 단락 위치 조정이 안 된다」).
        // 안쪽 표 다시 재기는 쪽 나누기 앞 맞춤(claude_sync_dirty_tac_tables)이 글자처럼 취급 바깥 표에서만 부르므로, 바깥 표가
        // 그렇지 않은 문서(문항카드의 쪽 크기 상자)를 위해 여기서 직접 부른다. 어긋남 값이 아직 없으면(열고 바로) 먼저 잰다.
        // 한/글 2024 실측: 그림을 21494 → 12896 으로 줄이면 안쪽 상자 24976 → 16378, 다음 문단 23694 → 15096(그림 높이 차만큼),
        // 바깥 표(글자처럼 취급 아님, 66825)는 그대로
        if path.len() > 1 {
            let cpi = path[path.len() - 1].2;
            self.reflow_cell_paragraph_by_path(section_idx, parent_para_idx, &path, cpi);
            self.recalculate_cell_paragraph_vpos_by_path(section_idx, parent_para_idx, &path, cpi, None);
            self.claude_init_measure_offsets();
            self.claude_sync_nested_tac(section_idx, parent_para_idx, path[0].0);
            if let Ok(t) = self.get_table_mut(section_idx, parent_para_idx, path[0].0) {
                t.dirty = true;
            }
            self.sync_tac_table_host_line(section_idx, parent_para_idx, path[0].0);
        }

        self.recompose_section(section_idx);
