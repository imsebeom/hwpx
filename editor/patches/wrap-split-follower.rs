// ==== find ====
        let has_ole_shape_square_wrap = para
// ==== replace ====
        // [claude-hwpx wrap-split-follower] 앞 문단의 어울림 그림 때문에 한 줄이 좌우 조각으로 갈라진 문단(떠 있는 그림,
        // 도형을 스스로 품지 않은 문단)도 조각 위치를 써야 한다. 폭 전체로 그리면 두 조각 글이 단 전체로 펼쳐져 서로,
        // 그리고 그림과 겹쳤다(한글이 저장한 문서도 같다 — 그림을 쪽 끝 문단 쪽으로 내린 경우, 2026-09-29).
        // 조각 위치에만 쓴다 — has_picture_shape_square_wrap 에 섞으면 빈 안내 줄 진행 생략까지 켜져, 그림 옆 빈 문단들의
        // 줄이 사라지고 뒤 표가 올라갔다
        let claude_split_follower = para.is_some_and(|p| {
            !p.controls.iter().any(|c| match c {
                Control::Picture(pic) => !pic.common.treat_as_char,
                Control::Shape(s) => !s.common().treat_as_char,
                _ => false,
            }) && (1..p.line_segs.len())
                .any(|idx| crate::renderer::height_measurer::stored_seg_is_row_fragment(p, idx))
        });
        let has_ole_shape_square_wrap = para
// ==== next ====
            let uses_stored_segment_geometry = (has_picture_shape_square_wrap
                || line_has_inline_tac_table
// ==== replace ====
            let uses_stored_segment_geometry = (has_picture_shape_square_wrap
                || claude_split_follower
                || line_has_inline_tac_table
// ==== next ====
            let precomputed_body_wrap_line = cell_ctx.is_none()
                && para_has_mixed_segment_widths
                && comp_line.segment_width > 0
                && line_avail_hu < col_area_w_hu - 200
// ==== replace ====
            // [claude-hwpx wrap-split-follower] 그림이 왼쪽에 있어 글이 오른쪽 조각에만 있는 줄은 시작 위치 + 폭이 단 폭과 같다.
            // 폭이 섞인 문단이면 그 오른쪽 조각(cs_significant)도 저장 위치로 그린다 — 단 전체로 펼쳐져 그림과 겹쳤다
            let precomputed_body_wrap_line = cell_ctx.is_none()
                && para_has_mixed_segment_widths
                && comp_line.segment_width > 0
                && (line_avail_hu < col_area_w_hu - 200 || cs_significant)
