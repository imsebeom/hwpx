// ==== find ====
        while cursor_line < line_count {
            let fn_margin = if st.current_footnote_height > 0.0 {
// ==== replace ====
        while cursor_line < line_count {
            // [claude-hwpx split-note-margin] HWPX 는 각주를 실제 줄로 재므로 안전 여유를 빼지 않는다(available_height 와 같게, 파트2 합본 7쪽)
            let fn_margin = if st.current_footnote_height > 0.0 && !st.profile.hwpx_container() {
