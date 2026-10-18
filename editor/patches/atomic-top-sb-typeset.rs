// ==== find ====
        if is_atomic_tac_singleton && st.current_height < available && !st.current_items.is_empty()
// ==== replace ====
        // [claude-hwpx atomic-top-sb] 개체 윗변은 위 간격 뒤다 — 위 간격까지 더해 본문 안인지 본다(d268 둘째 구역 p200, 한/글 새 조판)
        let claude_top_sb = if st.profile.hwpx_container() { fmt.spacing_before.max(0.0) } else { 0.0 };
        if is_atomic_tac_singleton
            && st.current_height + claude_top_sb < available
            && !st.current_items.is_empty()
