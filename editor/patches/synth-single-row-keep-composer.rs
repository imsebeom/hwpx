// ==== find ====
    if para.line_segs.len() >= 2
        && has_synthetic_line_segs
        && !para.stored_text_partition_is_dirty()
    {
// ==== replace ====
    // [claude-hwpx synth-single-row-keep] 엔진이 열 때 합성한(줄 폭이 있는) 한 줄도 경계를 그대로 둔다(d034 6쪽: 다시 나누면 한/글과 달리 두 줄)
    if (para.line_segs.len() >= 2
        || para.line_segs.first().is_some_and(|s| s.segment_width > 0))
        && has_synthetic_line_segs
        && !para.stored_text_partition_is_dirty()
    {
