// ==== find ====
        // clicked_cell 을 textbox_hit 보다 먼저 처리한다.
        if let Some((idx, offset)) = hit_cell {
// ==== replace ====
        // clicked_cell 을 textbox_hit 보다 먼저 처리한다.
        // [claude-hwpx nested-table-hit] 표 속 표를 품은 바깥 칸의 글 조각은 그 줄 높이만큼 커서 안쪽 표의
        // 빈 자리와 테두리까지 덮는다. 누른 칸이 그 조각보다 깊은 칸(같은 경로를 앞에 둔 자손)이면 조각을
        // 버리고 아래 칸 분기로 보낸다 — 안쪽 표 테두리 위에서 바깥 칸으로 캐럿이 가고 크기 조절이 안 뜨던 것.
        // 상류 devel e8b0e864b(#7442)와 같은 판정이다
        let hit_cell = hit_cell.filter(|&(idx, _)| {
            let deeper = cell_bboxes
                .iter()
                .filter(|cb| cb.has_meta)
                .filter(|cb| x >= cb.x && x <= cb.x + cb.w && y >= cb.y && y <= cb.y + cb.h)
                .min_by_key(|cb| ((cb.w.max(0.0) * cb.h.max(0.0)) * 1000.0) as i64)
                .and_then(|cb| cb.cell_context.as_ref());
            match (runs[idx].cell_context.as_ref(), deeper) {
                (Some(run_ctx), Some(cell_ctx)) => {
                    !(cell_ctx.parent_para_index == run_ctx.parent_para_index
                        && cell_ctx.path.len() > run_ctx.path.len()
                        && run_ctx.path.iter().zip(&cell_ctx.path).all(|(r, c)| {
                            r.control_index == c.control_index && r.cell_index == c.cell_index
                        }))
                }
                _ => true,
            }
        });
        if let Some((idx, offset)) = hit_cell {
