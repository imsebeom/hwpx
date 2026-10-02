// ==== find ====
            let cap = if ladder_omits_spacing {
                fmt.total_height
            } else {
                cap
            };
// ==== replace ====
            // [claude-hwpx tac-cap-ladder] 저장 스텝(다음 문단 vpos − 이 문단 vpos)이 fmt.total(줄 높이 + 줄 간격 전체)과
            // 1px 안에서 같으면 저장 사다리가 이 표 줄을 온전히 셈한 것이다 — cap(줄 높이 + 줄 간격 절반 + 바깥 위 여백)으로
            // 줄이지 않는다. 화면은 저장 vpos 로 그리는데 쪽 나누기만 표마다 2.2px 작게 세어, 쪽 끝 줄이 본문 아래로
            // 1.9px 넘쳐 그려졌다(2026-10-02 가이드북 3절 1쪽, 표 칸에 두 줄 넣으면 소제목 「2) 일차함수」 — 한/글은 2쪽으로)
            // 쪽 기준 좌표(다음 문단 위치가 본문 높이 안)일 때만 증거로 본다. 구역 처음부터 이어 센 좌표(rhwp, 생성기가 쓴 것,
            // 29쪽에서 1,685,544)는 rhwp 자신의 계산이라 늘 fmt.total 과 같다 — 거기 걸면 쪽을 꽉 채운 표 뒤 빈 문단이 다음 쪽으로
            // 밀렸다(한/글은 그 쪽에 둔다. 난산 최종보고서 p90, p96)
            let body_h_hu = crate::renderer::px_to_hwpunit(st.layout.body_area.height, self.dpi);
            let page_relative_ladder = para
                .line_segs
                .first()
                .zip(next_para.and_then(|np| np.line_segs.first()))
                .is_some_and(|(cur, next)| cur.vertical_pos >= 0 && next.vertical_pos <= body_h_hu);
            let ladder_matches_total = page_relative_ladder
                && stored_step_px
                    .is_some_and(|step| (step - fmt.total_height).abs() < 1.0 && step > cap + 0.5);
            let cap = if ladder_omits_spacing || ladder_matches_total {
                fmt.total_height
            } else {
                cap
            };
