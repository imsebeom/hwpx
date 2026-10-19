// ==== find ====
        let after = after
            + self.claude_multi_float_host_line_px(para, ctrl_idx);
// ==== replace ====
        let after = after
            + self.claude_multi_float_host_line_px(para, ctrl_idx);
        // [claude-hwpx full-square-empty] 열을 꽉 채우는 어울림 표의 빈 문단은 자리 차지 표처럼 바깥 여백만 쓰고 아래 간격, 줄 간격은 묻는다(d027 p0)
        let (before, after) = if self.profile.get().hwpx_container()
            && crate::renderer::claude_full_square_empty_host(para, table)
        {
            (
                hwpunit_to_px(table.outer_margin_top as i32, self.dpi),
                hwpunit_to_px(table.outer_margin_bottom as i32, self.dpi),
            )
        } else {
            (before, after)
        };
