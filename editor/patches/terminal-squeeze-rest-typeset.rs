// ==== find ====
                    && squeeze_rest <= TERMINAL_ROW_BOTTOM_SQUEEZE_MAX_REST_PX
// ==== replace ====
                    // [claude-hwpx terminal-squeeze-rest] HWPX 는 남은 자리 상한 없이 압축한다(d266 서약서 표: 남은 603px 에 선언 616px 행을 603px 로)
                    && (squeeze_rest <= TERMINAL_ROW_BOTTOM_SQUEEZE_MAX_REST_PX
                        || st.profile.hwpx_container())
