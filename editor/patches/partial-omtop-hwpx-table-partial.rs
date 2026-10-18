// ==== find ====
                crate::model::shape::VertRelTo::Para
            )
            && vert_off_signed > 0
        {
// ==== replace ====
                crate::model::shape::VertRelTo::Para
            )
            // [claude-hwpx partial-omtop-hwpx] HWPX 는 오프셋 0 인 첫 조각도 바깥 위 여백을 둔다(d072)
            && (vert_off_signed > 0 || (self.profile.get().hwpx_container() && vert_off_signed == 0))
        {
// ==== next ====
            let claude_outer_top = if paragraphs
                .get(para_index)
                .is_some_and(crate::renderer::para_has_no_stored_line_segs)
            {
// ==== replace ====
            let claude_outer_top = if self.profile.get().hwpx_container()
                || paragraphs
                    .get(para_index)
                    .is_some_and(crate::renderer::para_has_no_stored_line_segs)
            {
// ==== next ====
        } else if is_continuation
            && !table.common.treat_as_char
            && matches!(table.common.vert_rel_to, crate::model::shape::VertRelTo::Para)
            && paragraphs
                .get(para_index)
                .is_some_and(crate::renderer::para_has_no_stored_line_segs)
        {
// ==== replace ====
        } else if is_continuation
            && !table.common.treat_as_char
            && matches!(table.common.vert_rel_to, crate::model::shape::VertRelTo::Para)
            && (self.profile.get().hwpx_container()
                || paragraphs
                    .get(para_index)
                    .is_some_and(crate::renderer::para_has_no_stored_line_segs))
        {
