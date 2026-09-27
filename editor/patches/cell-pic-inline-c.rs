// ==== find ====
                    (new_ctrl_idx, logical_after)
                };

                self.mark_section_dirty(section_idx);
// ==== replace ====
                    (new_ctrl_idx, logical_after)
                };
                // [claude-hwpx cell-pic-inline-c] 칸 문단 줄 배치를 다시 계산하고, 글자처럼 취급 표면 표 높이와 표를 담은 줄 높이를 맞춘다
                if claude_inline && cell_path.len() == 1 {
                    let (tci, ci, cpi) = cell_path[0];
                    self.reflow_cell_paragraph(section_idx, para_idx, tci, ci, cpi);
                    self.sync_tac_table_host_line(section_idx, para_idx, tci);
                }

                self.mark_section_dirty(section_idx);
