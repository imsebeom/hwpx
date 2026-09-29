// ==== find ====
    let mut frame = host_box.frame_with(0, vec![exclusion]);
    let mut line_segs = Vec::new();

    for (paragraph_index, paragraph) in paragraphs.iter().enumerate().skip(host_index) {
        if frame.top >= exclusion_end {
            break;
        }

        let paragraph_style = styles.para_styles.get(paragraph.para_shape_id as usize);
// ==== replace ====
    let mut frame = host_box.frame_with(0, vec![exclusion]);
    let mut line_segs = Vec::new();
    // [claude-hwpx wrap-band-page-end] 편집 중에 그림이 쪽(단) 끝 문단보다 아래로 걸치면 다음 문단은 새 쪽, 새 단에서
    // 시작하므로 띠는 거기서 끝난다(한글도 그 문단까지만 비킨다). 종전에는 띠 전체를 포기해, 그림을 쪽 끝 문단 쪽으로
    // 끌어 내리면 두 문단이 옛 그림 자리의 좁은 줄을 그대로 갖고 남아 글이 그림과 겹쳤다(2026-09-29 사용자 발견).
    // 편집 경로(쪽 기하를 넘긴 호출)에서만 이렇게 한다 — 열 때의 on-demand 검증은 저장 줄 배치를 지키려고 거절을 유지한다
    let edit_context = crate::renderer::float_placement::CLAUDE_BAND_PAGE
        .with(|cell| cell.get())
        .is_some();
    let mut ended_at_break = false;

    for (paragraph_index, paragraph) in paragraphs.iter().enumerate().skip(host_index) {
        if frame.top >= exclusion_end {
            break;
        }

        let paragraph_style = styles.para_styles.get(paragraph.para_shape_id as usize);
        if edit_context
            && paragraph_index != host_index
            && (paragraph.column_type != ColumnBreakType::None
                || paragraph_style.is_some_and(|style| style.page_break_before))
        {
            ended_at_break = true;
            break;
        }
// ==== next ====
    (!line_segs.is_empty() && frame.top >= exclusion_end).then_some(PictureBandLayout {
// ==== replace ====
    let reached_end = edit_context && host_index + line_segs.len() == paragraphs.len();
    (!line_segs.is_empty() && (frame.top >= exclusion_end || ended_at_break || reached_end))
        .then_some(PictureBandLayout {
