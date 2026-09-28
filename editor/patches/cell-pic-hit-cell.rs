// ==== find ====
        if let Some((idx, offset)) = hit_cell {
            return Ok(format_hit(&runs[idx], offset, page_num));
        }
// ==== replace ====
        if let Some((idx, offset)) = hit_cell {
            // [claude-hwpx cell-pic-hit-cell] 글자 조각에 바로 맞은 경우도 그림만 있는 칸 문단이면 그림 상자로 정한다
            // (빈 글자 조각이 줄 끝까지 걸쳐, 둘째 그림 오른쪽을 눌러도 여기로 왔다)
            if let Some(ctx) = runs[idx].cell_context.as_ref().filter(|c| c.path.len() == 1) {
                let e = &ctx.path[0];
                if let Some((off, cx)) = self.claude_cell_pic_hit(
                    runs[idx].section_index,
                    ctx.parent_para_index,
                    e.control_index,
                    e.cell_index,
                    e.cell_para_index,
                    x,
                ) {
                    return Ok(Self::claude_hit_with_x(format_hit(&runs[idx], off, page_num), cx));
                }
            }
            return Ok(format_hit(&runs[idx], offset, page_num));
        }
