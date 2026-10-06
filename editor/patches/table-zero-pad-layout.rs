// ==== find ====
        // 축 단위로 동일해야 한다 (#1785 — 갈리면 예약 높이와 렌더가 어긋난다).
        let table_pad_unspec = !cell.apply_inner_margin
            && crate::model::table::Cell::table_padding_unspecified(&table.padding);
        let use_cell_left = Self::should_use_cell_padding_axis_for_context(
// ==== replace ====
        // 축 단위로 동일해야 한다 (#1785 — 갈리면 예약 높이와 렌더가 어긋난다).
        // [claude-hwpx table-zero-pad] HWPX 에서 읽은 표의 네 방향 0 은 진짜 0
        let table_pad_unspec = !cell.apply_inner_margin
            && crate::model::table::Cell::table_padding_unspecified_in(table);
        let use_cell_left = Self::should_use_cell_padding_axis_for_context(
