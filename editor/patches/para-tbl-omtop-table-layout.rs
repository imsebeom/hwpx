// ==== find ====
            let om_top_px = if matches!(vert_rel_to, crate::model::shape::VertRelTo::Paper) {
                hwpunit_to_px(table.outer_margin_top as i32, self.dpi)
// ==== replace ====
            // [claude-hwpx para-tbl-omtop] HWPX 는 문단 기준 표도 가시 윗변 = 기준 + 오프셋 + 바깥 위 여백(d322 1쪽 한/글 PDF 괘선 2.83pt 아래)
            let om_top_px = if matches!(vert_rel_to, crate::model::shape::VertRelTo::Paper)
                || (self.profile.get().hwpx_container()
                    && matches!(vert_rel_to, crate::model::shape::VertRelTo::Para))
            {
                hwpunit_to_px(table.outer_margin_top as i32, self.dpi)
