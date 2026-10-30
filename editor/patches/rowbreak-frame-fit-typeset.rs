// ==== find ====
            && next_starts_new_page
            && !rowbreak_table_has_internal_saved_vpos_reset(table))
// ==== replace ====
            && next_starts_new_page
            && !rowbreak_table_has_internal_saved_vpos_reset(table)
            // [claude-hwpx rowbreak-frame-fit] 잰 표가 적힌 높이(첫 조각) 안에 들 때만 — 더 크면 행을 다음 쪽으로 이어야 한다(d022 71행: 적힌 599px, 잰 2272px)
            && table_total - host_spacing_total <= declared_object_total - host_spacing_total + 1.0)
