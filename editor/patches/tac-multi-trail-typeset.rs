// ==== find ====
        let is_tac = self.is_effective_tac_table(para, table, fmt);
        if is_tac && fmt.total_height > fmt.height_for_fit && !has_post_text {
// ==== replace ====
        let is_tac = self.is_effective_tac_table(para, table, fmt);
        // [claude-hwpx tac-multi-trail] 뒤에 글자처럼 취급 표가 더 있으면 이 표 높이에 줄 간격이 이미 들어 있다(typeset_tac_table 의 is_last_tac)
        let claude_later_tac = st.profile.hwpx_container()
            && para.controls.iter().skip(ctrl_idx + 1).any(
                |c| matches!(c, Control::Table(t) if self.is_effective_tac_table(para, t, fmt)),
            );
        if is_tac && fmt.total_height > fmt.height_for_fit && !has_post_text && !claude_later_tac {
