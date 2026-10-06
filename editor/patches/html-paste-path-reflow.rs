// ==== find ====
            )?
        };

        let outer_ctrl = path[0].0;
// ==== replace ====
            )?
        };

        // [claude-hwpx html-paste-path-reflow] 내부 클립보드 경로판(#2825)과 같이 붙인 문단을 칸 폭으로 다시 나누고 뒤 문단 세로 위치를
        // 다시 매긴다. 종전에는 HTML 붙이기 경로판만 빠져, 칸에 긴 글을 붙이면 한 줄짜리 옛 줄 배치가 남아 글이 한 줄에 눌려 그려졌다
        // (2026-10-06 CORE 실적표 칸 붙이기: 두 줄 글이 한 줄로)
        for i in cell_para_idx..=last_para_idx {
            self.reflow_cell_paragraph_by_path(section_idx, parent_para_idx, path, i);
        }
        self.recalculate_cell_paragraph_vpos_by_path(section_idx, parent_para_idx, path, cell_para_idx, None);

        let outer_ctrl = path[0].0;
