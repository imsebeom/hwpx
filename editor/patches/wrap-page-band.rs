// ==== find ====
    let exclusion = crate::renderer::float_placement::resolve_picture_exclusion(
        picture,
        column_horizontal.clone(),
        host_paragraph_horizontal,
        anchor_top,
    )?;
// ==== replace ====
    // [claude-hwpx wrap-page-band] 문단 기준이 아닌(쪽, 종이 기준) 그림은 편집 쪽이 넘긴 쪽 기하로 제외 영역을 만든다
    let exclusion = crate::renderer::float_placement::resolve_picture_exclusion(
        picture,
        column_horizontal.clone(),
        host_paragraph_horizontal.clone(),
        anchor_top,
    )
    .or_else(|| {
        crate::renderer::float_placement::claude_page_picture_exclusion(
            picture,
            &column_horizontal,
            &host_paragraph_horizontal,
            anchor_top,
        )
    })?;
