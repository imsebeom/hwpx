// ==== find ====
            let splittable = can_intra_split
                && (mt.is_row_splittable(r) || native_short_parent_child_splittable);
// ==== replace ====
            let splittable = can_intra_split
                && (mt.is_row_splittable(r) || native_short_parent_child_splittable)
                // [claude-hwpx table-whole-rows] 「표 나눔」(CellBreak) 표는 쪽 첫 행이 아니면 행을 통째로 다음 쪽에 넘긴다(한/글 2024 실측)
                && !(matches!(table.page_break, crate::model::table::TablePageBreak::CellBreak) && r > cursor_row);
