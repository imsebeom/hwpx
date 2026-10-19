// ==== find ====
         -> Option<CursorHit> {
            if let Some(target) = cell_target {
                find_cell_cursor(&tree.root, target, para_idx, offset, page, bias)
            } else {
                find_body_cursor(
                    &tree.root,
                    section_idx,
                    para_idx,
                    self.get_render_paragraph_ref(section_idx, para_idx).ok(),
                    offset,
                    page,
                    bias,
                )
            }
        };
// ==== replace ====
         -> Option<CursorHit> {
            let claude_find = |bias: CursorBias| {
            if let Some(target) = cell_target {
                find_cell_cursor(&tree.root, target, para_idx, offset, page, bias)
            } else {
                find_body_cursor(
                    &tree.root,
                    section_idx,
                    para_idx,
                    self.get_render_paragraph_ref(section_idx, para_idx).ok(),
                    offset,
                    page,
                    bias,
                )
            }
            };
            // [claude-hwpx note-caret-axis] 선택 시작이 각주 표지 자리(표지 앞 캐럿)면 표지부터 칠한다 — 앞 글자 조각이 같은 줄에서
            // 표지 폭(글자 크기 1.5배 안)만큼 왼쪽에서 끝나면 그 끝을 쓴다. 칸 안 표지 노드는 칸 정보가 없어 조각 끝으로 찾는다
            let hit = claude_find(bias)?;
            if matches!(bias, CursorBias::Leading) {
                if let Some(t) = claude_find(CursorBias::Trailing) {
                    if t.page == hit.page
                        && (t.y - hit.y).abs() < 1.0
                        && t.x < hit.x - 0.5
                        && hit.x - t.x < hit.h * 1.5
                    {
                        return Some(CursorHit { x: t.x, ..hit });
                    }
                }
            }
            Some(hit)
        };
