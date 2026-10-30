// ==== find ====
                && self.cell_has_square_float.get()
                && comp_line.column_start > 0
                && comp_line.segment_width > 0
                && comp_line.segment_width < col_area_w_hu;
// ==== replace ====
                && self.cell_has_square_float.get()
                // [claude-hwpx cell-square-right] 오른쪽 그림은 줄 시작이 0 이다 — 여백을 뺀 폭보다 1200 넘게 좁으면 그림 때문이다(자료 1 칸: 뒤 문단이 그림과 겹침)
                && (comp_line.column_start > 0
                    || (self.profile.get().hwpx_container()
                        && comp_line.segment_width
                            < col_area_w_hu
                                - crate::renderer::px_to_hwpunit(margin_left + margin_right, self.dpi)
                                - 1200))
                && comp_line.segment_width > 0
                && comp_line.segment_width < col_area_w_hu;
