// ==== find ====
            st.vpos_ladder_dirty = false;
        }
        let mut hc = HeightCursor {
            dpi: self.dpi,
            col_area_y: 0.0,
// ==== replace ====
            st.vpos_ladder_dirty = false;
        }
        // [claude-hwpx synth-no-snap] 엔진이 만든 줄(저장 줄 배치가 아닌 줄)의 vpos 로는 누적 높이를 되맞추지 않는다. 편집 경로
        // (쪽 설정, 표 넣기, 캡션 등)는 줄을 새로 만든 뒤 vpos 사슬을 다시 잇지 않아 0 이나 낡은 값이 남고, 스냅이 그 값으로 쪽을
        // 틀었다(2026-10-18 사용자 보고 「에디터가 고치면 쪽이 어긋난다」, editor/tests/edit_consistency.mjs). 열기 경로의 사슬에
        // 문단 간격을 넣은 뒤(synth-vpos-spacing)에는 정답본 채점도 쪽수 93.6 → 93.9%, 문단 쪽 그대로
        if paragraphs.get(para_idx).and_then(|p| p.line_segs.first()).is_some_and(|s| {
                s.tag & crate::model::paragraph::LineSeg::TAG_IMPLEMENTATION_PROPERTY != 0
            })
        {
            return;
        }
        let mut hc = HeightCursor {
            dpi: self.dpi,
            col_area_y: 0.0,
