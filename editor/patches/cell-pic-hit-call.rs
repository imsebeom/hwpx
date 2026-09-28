// ==== find ====
                    let (idx, offset) = resolve_x_on_line(&line_runs, x);
                    return Ok(format_hit(line_runs[idx], offset, page_num));
// ==== replace ====
                    let (idx, offset) = resolve_x_on_line(&line_runs, x);
                    // [claude-hwpx cell-pic-hit] 그림만 있는 칸 문단은 그림 상자로 자리와 캐럿 x 를 정한다
                    if let Some(ctx) = line_runs[idx].cell_context.as_ref().filter(|c| c.path.len() == 1) {
                        let e = &ctx.path[0];
                        if let Some((off, cx)) = self.claude_cell_pic_hit(
                            line_runs[idx].section_index,
                            ctx.parent_para_index,
                            e.control_index,
                            e.cell_index,
                            e.cell_para_index,
                            x,
                        ) {
                            return Ok(Self::claude_hit_with_x(format_hit(line_runs[idx], off, page_num), cx));
                        }
                    }
                    return Ok(format_hit(line_runs[idx], offset, page_num));
