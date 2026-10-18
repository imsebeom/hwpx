// ==== find ====
            let skip_advance_empty_wrap = has_picture_shape_square_wrap
                && !has_ole_shape_square_wrap
                && runs_all_whitespace
                && !line_has_tac_control(composed, line_idx);
// ==== replace ====
            let skip_advance_empty_wrap = has_picture_shape_square_wrap
                && !has_ole_shape_square_wrap
                && runs_all_whitespace
                && !line_has_tac_control(composed, line_idx)
                // [claude-hwpx square-empty-host-line] 글 없는 앵커 문단의 줄은 HWPX 에서 진행한다(조판과 같은 판정)
                && !(self.profile.get().hwpx_container() && para.is_some_and(|p| p.text.trim().is_empty()));
