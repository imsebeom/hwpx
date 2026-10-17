// ==== find ====
        HorzAlign::Center => ref_x + (ref_w - width_px).max(0.0) / 2.0 + h_offset,
// ==== replace ====
        // [claude-hwpx wide-table-column-center-float] 표 그리기(wide-table-column-center)와 같은 가로 범위
        HorzAlign::Center if matches!(common.horz_rel_to, HorzRelTo::Column) => {
            ref_x + (ref_w - width_px) / 2.0 + h_offset
        }
        HorzAlign::Center => ref_x + (ref_w - width_px).max(0.0) / 2.0 + h_offset,
