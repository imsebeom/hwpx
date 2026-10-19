// ==== find ====
            allow_large_backward,
            self.dpi,
        );
        let prev_line_spacing_px
// ==== replace ====
            allow_large_backward,
            self.dpi,
        );
        // [claude-hwpx float-host-backward] 앞 문단이 표만 담은 문단 기준 자리 차지 표 호스트면 이 문단 위 간격은 표 아래에 묻힌다 — 그만큼 뒤로 당겨도 된다(d189 p6)
        let claude_prev_float_host = !para_has_visible_text(prev_para)
            && prev_para.controls.iter().any(|c| {
                matches!(c, Control::Table(t)
                    if !t.common.treat_as_char
                        && matches!(t.common.text_wrap, TextWrap::TopAndBottom)
                        && matches!(t.common.vert_rel_to, crate::model::shape::VertRelTo::Para))
            });
        let applied = applied
            || (claude_prev_float_host
                && end_y >= y_offset - curr_sb - 8.0
                && end_y >= self.col_area_y
                && end_y <= self.col_area_y + self.col_area_height);
        let prev_line_spacing_px
