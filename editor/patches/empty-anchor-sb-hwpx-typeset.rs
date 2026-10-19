// ==== find ====
        let before = if !is_tac
            && table_wrap_take_place
// ==== replace ====
        // [claude-hwpx empty-anchor-sb-hwpx] HWPX 빈 앵커 자리 차지 표는 다음 항목과 상관없이 위 간격을 쓰지 않는다(한/글 새 조판 24/24)
        let before = if self.profile.get().hwpx_container() && !is_tac && is_topbottom_empty_anchor {
            outer_top
        } else if !is_tac
            && table_wrap_take_place
