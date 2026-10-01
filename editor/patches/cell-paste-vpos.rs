// ==== find ====
        for i in cell_para_idx..=last_para_idx {
            self.reflow_cell_paragraph_by_path(section_idx, parent_para_idx, path, i);
        }
// ==== replace ====
        for i in cell_para_idx..=last_para_idx {
            self.reflow_cell_paragraph_by_path(section_idx, parent_para_idx, path, i);
        }
        // [claude-hwpx cell-paste-vpos] 다시 나눈 문단의 높이가 바뀌면 칸 안 뒤 문단의 세로 위치도 다시 매긴다. 종전에는 옛 위치에
        // 남아, 칸 문단에 그림을 붙이면 뒤 문단이 그 문단과 겹쳐 순서가 뒤섞여 보였다(2026-10-02)
        self.recalculate_cell_paragraph_vpos_by_path(section_idx, parent_para_idx, path, cell_para_idx, None);
