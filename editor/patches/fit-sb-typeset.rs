// ==== find ====
            omit_untrusted_empty || strict_after_empty_host_float,
        );
// ==== replace ====
            omit_untrusted_empty || strict_after_empty_host_float,
        );
        // [claude-hwpx fit-sb] 한/글은 쪽 끝 맞춤에 위 간격을 센다(정답본 15/15, lab exp/harvest_fit_sb.py).
        // height_for_fit 은 줄 배치 폭이라 위 간격이 빠져 있다 — 비교에만 더하고 흐름 전진은 그대로 둔다.
        // 빈 문단은 쪽 바닥을 넘어도 그 쪽에 남는다(d321 p66, p124, d330 p30, p31) — 더하지 않는다.
        let page_end_fit_height = if st.profile.hwpx_container() && st.col_count == 1 && para_has_visible_text(para) {
            let trail = fmt.line_spacings.last().copied().unwrap_or(0.0);
            page_end_fit_height.max(
                (fmt.height_for_fit + fmt.spacing_before.max(0.0)).min((fmt.total_height - trail).max(0.0)),
            )
        } else {
            page_end_fit_height
        };
