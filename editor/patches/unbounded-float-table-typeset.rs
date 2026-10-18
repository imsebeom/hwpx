// ==== find ====
        if st.current_height + whole_fit_table_total <= available
            || fits_after_overlay_shapes
// ==== replace ====
        // [claude-hwpx unbounded-float-table] 나누지 않음 + flowWithText=0 인 문단 기준 위아래 배치 표는 한/글이 다음 쪽으로 넘기지 않고 그 쪽에 넘쳐 둔다
        // (d193 p57 실험: 빈 문단으로 용지 밖까지 밀어도 그대로, flowWithText=1 이거나 나눔이 CELL, TABLE 이면 넘긴다)
        let claude_unbounded_float = st.profile.hwpx_container()
            && !table.common.treat_as_char
            && !table.common.flow_with_text
            && matches!(table.page_break, crate::model::table::TablePageBreak::None)
            && matches!(table.common.text_wrap, TextWrap::TopAndBottom)
            && matches!(table.common.vert_rel_to, VertRelTo::Para)
            && !st.current_items.is_empty()
            && table_total <= st.base_available_height();
        if st.current_height + whole_fit_table_total <= available
            || claude_unbounded_float
            || fits_after_overlay_shapes
