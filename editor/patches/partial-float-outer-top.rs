// ==== find ====
            (hwpunit_to_px(vert_off_signed, self.dpi) - pre_emitted_host_height).max(0.0)
        } else {
            0.0
        };
// ==== replace ====
            // [claude-hwpx partial-float-outer-top] 줄 배치 없는 문단(스킬 산출물)의 쪽에 걸친 표는 한/글처럼 첫 조각을 바깥 위
            // 여백만큼 내리고, 이어지는 조각도 쪽 맨 위에 그 여백을 다시 둔다(empty-float-outer-top 의 나뉜 표 판. 2026-10-17
            // 교과 평가계획 영어과 표: 7쪽 첫 조각 2.9px 높고, 8쪽 이어진 조각 괘선이 한/글 86.1px, rhwp 83.6px)
            let claude_outer_top = if paragraphs
                .get(para_index)
                .is_some_and(crate::renderer::para_has_no_stored_line_segs)
            {
                hwpunit_to_px(table.outer_margin_top as i32, self.dpi)
            } else {
                0.0
            };
            (hwpunit_to_px(vert_off_signed, self.dpi) - pre_emitted_host_height).max(0.0)
                + claude_outer_top
        } else if is_continuation
            && !table.common.treat_as_char
            && matches!(table.common.vert_rel_to, crate::model::shape::VertRelTo::Para)
            && paragraphs
                .get(para_index)
                .is_some_and(crate::renderer::para_has_no_stored_line_segs)
        {
            hwpunit_to_px(table.outer_margin_top as i32, self.dpi)
        } else {
            0.0
        };
