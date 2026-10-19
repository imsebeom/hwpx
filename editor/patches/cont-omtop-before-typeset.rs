// ==== find ====
            // [#6143] 오프셋이 쪽 경계에서 이미 소진된 첫 조각은 예산에서도 빼지
// ==== replace ====
            // [claude-hwpx cont-omtop-before] HWPX 이어지는 조각은 쪽 위에 바깥 위 여백을 두고 그린다(partial-omtop-hwpx) — 조판도 센다(d075 6쪽)
            let host_before_overhead = if self.profile.get().hwpx_container()
                && is_continuation
                && host_before_overhead == 0.0
                && !table.common.treat_as_char
                && is_para_topbottom_float(&table.common)
                && matches!(
                    table.page_break,
                    crate::model::table::TablePageBreak::RowBreak
                )
                && table.cells.iter().all(|c| {
                    c.paragraphs.iter().all(crate::renderer::para_has_no_stored_line_segs)
                }) {
                hwpunit_to_px(table.outer_margin_top as i32, self.dpi)
            } else {
                host_before_overhead
            };
            // [#6143] 오프셋이 쪽 경계에서 이미 소진된 첫 조각은 예산에서도 빼지
