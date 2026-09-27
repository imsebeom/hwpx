// ==== find ====
                self.reflow_cell_paragraph_by_path(*section_idx, *parent_para, path, inner_para);
// ==== replace ====
                self.reflow_cell_paragraph_by_path(*section_idx, *parent_para, path, inner_para);
                // [claude-hwpx replace-cell-dirty] 바꾸기로 칸 글이 바뀌면 바깥 표에 dirty 를 켠다. 켜지 않으면 측정 캐시를
                // 그대로 써 표가 늘지 않고, 쪽 나누기 전 표 높이 맞춤(tac-host-sync-paginate)도 걸리지 않았다(2026-09-27)
                if let Some(first) = path.first() {
                    self.mark_cell_control_dirty(*section_idx, *parent_para, first.0);
                }
