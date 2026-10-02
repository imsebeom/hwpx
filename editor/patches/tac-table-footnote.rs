// ==== find ====
        // TAC 표는 분할하지 않고 통째로 배치
        let available = st.available_height();
// ==== replace ====
        // TAC 표는 분할하지 않고 통째로 배치
        // [claude-hwpx tac-table-footnote] 칸 안에 각주가 든 글자처럼 취급 표는 그 각주가 이 쪽 아래에 더할 높이(구분선 포함)를
        // 빼고 맞춘다. 블록 표(typeset_block_table_inner)는 이미 이렇게 하는데 이 경로만 빠져, 표를 쪽 맨 아래까지 앉힌 뒤
        // 각주가 붙어 표와 겹쳤다(2026-10-02 가이드북 3절 표 3-2, 표 바닥 1027px, 각주 1016px). 각주 안전 여유(footnote_safety_margin)는
        // 빼지 않는다 — 넣으면 한/글이 같은 쪽에 두는 표(같은 원고 _06, 표 바닥 992px)까지 다음 쪽으로 밀었다
        let available = {
            let base = st.available_height();
            if ft.table_footnote_count == 0 {
                base
            } else {
                let reclaim = st.footer_band_reclaim();
                let projected =
                    st.projected_footnote_height(ft.table_footnote_height, ft.table_footnote_count);
                let extra = (projected - reclaim).max(0.0) - (st.current_footnote_height - reclaim).max(0.0);
                (base - extra).max(0.0)
            }
        };
