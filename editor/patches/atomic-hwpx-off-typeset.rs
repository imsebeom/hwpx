// ==== find ====
        if is_atomic_tac_singleton
            && st.current_height + claude_top_sb < available
// ==== replace ====
        // [claude-hwpx atomic-hwpx-off] HWPX 는 넘쳐 담지 않는다(한/글 새 조판 14/14 다음 쪽, 넘쳐 담음 0)
        if is_atomic_tac_singleton
            && !st.profile.hwpx_container()
            && st.current_height + claude_top_sb < available
