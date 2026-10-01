// ==== find ====
                if claude_inline && cell_path.len() == 1 {
                    let (tci, ci, cpi) = cell_path[0];
                    self.reflow_cell_paragraph(section_idx, para_idx, tci, ci, cpi);
                    self.sync_tac_table_host_line(section_idx, para_idx, tci);
                }
// ==== replace ====
                if claude_inline && cell_path.len() == 1 {
                    let (tci, ci, cpi) = cell_path[0];
                    self.reflow_cell_paragraph(section_idx, para_idx, tci, ci, cpi);
                    // 칸 안 뒤 문단의 세로 위치도 다시 매긴다(그림이 든 문단이 커진 만큼. 종전에는 겹쳤다)
                    self.recalculate_cell_paragraph_vpos_by_path(section_idx, para_idx, &cell_path.to_vec(), cpi, None);
                    self.sync_tac_table_host_line(section_idx, para_idx, tci);
                } else if claude_inline && cell_path.len() > 1 {
                    // [claude-hwpx cell-pic-nested] 표 속 표 칸이면 안쪽 칸 폭으로 줄을 다시 나누고, 맨 바깥 표를 편집한 표로 표시해
                    // 쪽 나누기 시작에 표 높이를 맞추게 한다(tac-host-sync-paginate). 종전에는 줄 배치가 옛것 그대로라 그림이 한 줄에 눌렸다
                    let path: Vec<(usize, usize, usize)> = cell_path.to_vec();
                    let cpi = path[path.len() - 1].2;
                    self.reflow_cell_paragraph_by_path(section_idx, para_idx, &path, cpi);
                    self.recalculate_cell_paragraph_vpos_by_path(section_idx, para_idx, &path, cpi, None);
                    if let Ok(t) = self.get_table_mut(section_idx, para_idx, path[0].0) {
                        t.dirty = true;
                    }
                    self.sync_tac_table_host_line(section_idx, para_idx, path[0].0);
                }
