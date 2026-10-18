// ==== find ====
                    let avail = st.available_height() - st.current_height;
                    if empty_h_px > avail {
                        // [#1706] 빈 paragraph 가 fit 안 됨.
// ==== replace ====
                    let avail = st.available_height() - st.current_height;
                    // [claude-hwpx empty-before-break] 순수 HWPX(한/글 2024 저장본)는 안 들어가는 빈 문단을 다음 쪽으로 넘긴다(정답본 11곳 중 9곳, d078).
                    // 아래 흡수는 HWP5 표본(sample18) 규칙이라 HWP5 출처에만 둔다
                    let claude_pure_hwpx = st.profile.hwpx_container() && !st.profile.hwp5_stored_pagination_layout();
                    if empty_h_px > avail && !claude_pure_hwpx {
                        // [#1706] 빈 paragraph 가 fit 안 됨.
