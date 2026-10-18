// ==== find ====
                    let nested_atom_tail = self.nested_atom_invisible_tail(cell, u, styles);
                    if nested_atom_tail > 0.0 && h + u.height - nested_atom_tail <= avail_height {
// ==== replace ====
                    // [claude-hwpx cell-cut-trailing-spacing] 마지막으로 담는 줄의 뒤 줄 간격은 쪽 끝을 넘어도 된다(d243: 한/글이 교사 칸 4줄을 담는다)
                    if self.profile.get().hwpx_container()
                        && !u.empty_spacer
                        && u.nested_row.is_none()
                        && u.nested_table_fragment.is_none()
                        && u.vis_end == u.vis_start + 1
                        // 칸의 마지막 줄 유닛은 높이에 줄 간격이 없다(d191, d014 에서 두 번 빼 행이 들어간다고 오판)
                        && j + 1 < units.len()
                    {
                        let claude_tail = cell
                            .paragraphs
                            .get(u.para_idx)
                            .and_then(|p| p.line_segs.get(u.vis_start))
                            .map(|s| hwpunit_to_px(s.line_spacing.max(0), self.dpi))
                            .unwrap_or(0.0)
                            .min(u.height);
                        if claude_tail > 0.0
                            && h + u.height - claude_tail <= avail_height + ROW_CUT_CAPACITY_FP_EPSILON_PX
                        {
                            h += u.height - claude_tail;
                            j += 1;
                            break;
                        }
                    }
                    let nested_atom_tail = self.nested_atom_invisible_tail(cell, u, styles);
                    if nested_atom_tail > 0.0 && h + u.height - nested_atom_tail <= avail_height {
