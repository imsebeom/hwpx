// ==== find ====
                    r == cursor_row
                        || (res.hit_hard_break && res.consumed_height >= MIN_TOP_KEEP_PX)
// ==== replace ====
                    r == cursor_row
                        // [claude-hwpx hard-break-keep] HWPX 는 저장된 나눔 자리를 믿는다(d129: 첫 조각 23.5px 로 거절되면 1쪽 는다)
                        || (res.hit_hard_break
                            && (res.consumed_height >= MIN_TOP_KEEP_PX
                                || (st.profile.hwpx_container() && res.consumed_height > 0.0)))
