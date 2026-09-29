// ==== find ====
    let exclusion_end = exclusion.vertical.end;
    let mut frame = host_box.frame_with(0, vec![exclusion]);
// ==== replace ====
    // [claude-hwpx wrap-band-backward] 편집 중에 쪽, 종이 기준 그림을 그림을 품은 문단보다 위로 옮기면 그림이 앞 문단들에
    // 걸친다. 한글은 그 앞 문단들도 비키게 하는데 띠가 호스트부터만 짜서 앞 문단이 그림 밑으로 겹쳤다(2026-09-30 대조).
    // 같은 쪽(단) 안에서 그림 상자에 걸치는 앞 문단까지 거슬러 올라가 거기서 띠를 시작하고, 제외 영역을 그 문단 좌표로 옮긴다
    let mut exclusion = exclusion;
    let mut band_start = host_index;
    if crate::renderer::float_placement::CLAUDE_BAND_PAGE
        .with(|cell| cell.get())
        .is_some()
        && exclusion.vertical.start < 0
    {
        if let Some(host_top) = host.line_segs.first().map(|seg| seg.vertical_pos) {
            let box_top = host_top.saturating_add(exclusion.vertical.start);
            let mut first = host_index;
            while first > 0 && paragraphs[first].column_type == ColumnBreakType::None {
                let previous = &paragraphs[first - 1];
                let (Some(previous_top), Some(previous_end)) = (
                    previous.line_segs.first().map(|seg| seg.vertical_pos),
                    paragraph_flow_end(previous),
                ) else {
                    break;
                };
                // 앞 문단이 그림 위에서 끝났거나, 쪽이 바뀌어 세로 위치가 다시 0 부터 시작했으면 멈춘다
                if previous_end <= box_top || previous_top > host_top {
                    break;
                }
                first -= 1;
            }
            if first < host_index {
                let shift = host_top.saturating_sub(paragraphs[first].line_segs[0].vertical_pos);
                exclusion.vertical =
                    exclusion.vertical.start.saturating_add(shift)..exclusion.vertical.end.saturating_add(shift);
                band_start = first;
            }
        }
    }
    let exclusion_end = exclusion.vertical.end;
    let mut frame = host_box.frame_with(0, vec![exclusion]);
// ==== next ====
    for (paragraph_index, paragraph) in paragraphs.iter().enumerate().skip(host_index) {
        if frame.top >= exclusion_end {
            break;
        }

        let paragraph_style = styles.para_styles.get(paragraph.para_shape_id as usize);
        if edit_context
            && paragraph_index != host_index
// ==== replace ====
    for (paragraph_index, paragraph) in paragraphs.iter().enumerate().skip(band_start) {
        // 그림이 호스트보다 위에서 끝나도 호스트까지는 띠에 넣는다(띠는 호스트가 소유한다)
        if frame.top >= exclusion_end && paragraph_index > host_index {
            break;
        }

        let paragraph_style = styles.para_styles.get(paragraph.para_shape_id as usize);
        // 편집 경로에서는 띠 첫 문단이 쪽(단)을 여는 문단이어도 받는다(세로 위치는 편집 쪽이 0 부터 다시 매긴다)
        let starts_band = edit_context && paragraph_index == band_start;
        if edit_context
            && paragraph_index != band_start
// ==== next ====
        if paragraph.column_type != ColumnBreakType::None
            || paragraph_style.is_some_and(|style| {
                style.spacing_before.abs() > f64::EPSILON
                    || style.spacing_after.abs() > f64::EPSILON
                    || style.page_break_before
            })
// ==== replace ====
        if (paragraph.column_type != ColumnBreakType::None && !starts_band)
            || paragraph_style.is_some_and(|style| {
                style.spacing_before.abs() > f64::EPSILON
                    || style.spacing_after.abs() > f64::EPSILON
                    || (style.page_break_before && !starts_band)
            })
// ==== next ====
    let reached_end = edit_context && host_index + line_segs.len() == paragraphs.len();
    (!line_segs.is_empty() && (frame.top >= exclusion_end || ended_at_break || reached_end))
        .then_some(PictureBandLayout {
        paragraph_range: host_index..host_index + line_segs.len(),
// ==== replace ====
    let reached_end = edit_context && band_start + line_segs.len() == paragraphs.len();
    // 띠가 호스트에 닿기 전에 끝나면(앞 문단만 걸친 경우도 호스트는 띠에 넣어야 한다) 호스트까지 이어진 경우만 받는다
    (!line_segs.is_empty()
        && band_start + line_segs.len() > host_index
        && (frame.top >= exclusion_end || ended_at_break || reached_end))
        .then_some(PictureBandLayout {
        paragraph_range: band_start..band_start + line_segs.len(),
