// ==== find ====
    omit_fresh_recalc_doc: bool,
    /// [#5699 H1]
// ==== replace ====
    omit_fresh_recalc_doc: bool,
    /// [claude-hwpx stale-reset-fill] 이 구역에서 낡은 저장 리셋을 한 번 무시했는가. 그 뒤로는 저장 좌표의
    /// 쪽 원점이 rhwp 쪽과 어긋나 있어, 다음 리셋의 「저장 좌표가 쪽을 채웠다」는 증거를 믿지 않는다
    claude_stale_reset_seen: bool,
    /// [#5699 H1]
// ==== next ====
            omit_fresh_recalc_doc: false,
            ladder_band_floor: 0.0,
            current_ladder_band_tables: Vec::new(),
// ==== replace ====
            omit_fresh_recalc_doc: false,
            claude_stale_reset_seen: false,
            ladder_band_floor: 0.0,
            current_ladder_band_tables: Vec::new(),
// ==== next ====
                    let trigger = trigger
                        && !omit_pushed_empty_page
                        && !hangul2024_refit
                        && !overlay_columndef_separator_break;
// ==== replace ====
                    // [claude-hwpx stale-reset-fill] 저장 리셋(vpos=0)이 쪽을 넘기라고 해도, 저장 좌표가 그 쪽을 채웠다고
                    // 말하지 않고(직전 문단 끝이 본문 높이의 50% 미만이거나 110% 초과 — 쪽 기준 좌표가 아니다) 이 쪽도
                    // 반이 비었으면 따르지 않고 자리 계산에 맡긴다. 낡은 리셋: 에디터 저장본에 rhwp 의 구역 연속 좌표가
                    // 섞여(2026-10-02 가이드북 3절 표 3-1, 직전 끝 152279 > 본문 70016) 표가 4쪽을 21%만 채우고 넘어갔고,
                    // 줄 배치를 지어내는 생성기 산출물(직전 끝 8000)은 쪽마다 끊겼다. 한글이 끊은 리셋은 직전 끝이
                    // 본문의 90~105% 라 그대로 따른다 — rhwp 가 높이를 작게 재어 반도 안 찼다고 볼 때도 마찬가지다.
                    // 한 번 무시한 뒤로는 저장 좌표의 쪽 원점이 어긋나 있어 그 증거를 보지 않는다(같은 문서 p49)
                    let claude_low_fill_reset = trigger && st.col_count == 1 && {
                        let body_hu =
                            crate::renderer::px_to_hwpunit(st.layout.body_area.height, self.dpi);
                        let stored_unfit = st.claude_stale_reset_seen
                            || prev_vpos_end < body_hu / 2
                            || prev_vpos_end > body_hu.saturating_mul(11) / 10;
                        stored_unfit && st.current_height < st.available_height() * 0.5
                    };
                    if claude_low_fill_reset {
                        st.claude_stale_reset_seen = true;
                    }
                    if std::env::var("RHWP_DIAG_STALE").is_ok() && claude_low_fill_reset {
                        eprintln!(
                            "DIAG_STALE low-fill reset pi={para_idx} cur={:.1} avail={:.1} prev_end={prev_vpos_end}",
                            st.current_height,
                            st.available_height(),
                        );
                    }
                    let trigger = trigger
                        && !omit_pushed_empty_page
                        && !hangul2024_refit
                        && !overlay_columndef_separator_break
                        && !claude_low_fill_reset;
