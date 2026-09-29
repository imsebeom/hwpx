// ==== find ====
    let common = &picture.common;
    if common.treat_as_char
        || picture.caption.is_some()
        || common.text_wrap != TextWrap::Square
        || !matches!(common.horz_rel_to, HorzRelTo::Column | HorzRelTo::Para)
        || common.vert_rel_to != VertRelTo::Para
        || !matches!(common.vert_align, VertAlign::Top | VertAlign::Inside)
    {
        return None;
    }
    let policy = match common.text_flow {
        TextFlow::BothSides => FrameExclusionPolicy::BothSides,
        TextFlow::LargestOnly => FrameExclusionPolicy::LargestSide,
        TextFlow::LeftOnly | TextFlow::RightOnly => return None,
    };
// ==== replace ====
    let common = &picture.common;
    // [claude-hwpx wrap-exclusion] 편집 뒤 그림 띠가 받는 배치를 넓힌다. 종전에는 어울림 + 양쪽/큰 쪽만 받아
    // 자리 차지, 어울림 왼쪽/오른쪽 그림 옆 문단은 편집하면 그림을 무시하고 줄을 다시 짜 글이 그림 밑으로 겹쳤다.
    // 자리 차지는 단 폭 전체를 막는 제외 영역이라 줄이 그림 아래로 내려간다
    let top_and_bottom = common.text_wrap == TextWrap::TopAndBottom;
    if common.treat_as_char
        || picture.caption.is_some()
        || !(common.text_wrap == TextWrap::Square || top_and_bottom)
        || !matches!(common.horz_rel_to, HorzRelTo::Column | HorzRelTo::Para)
        || common.vert_rel_to != VertRelTo::Para
        || !matches!(common.vert_align, VertAlign::Top | VertAlign::Inside)
    {
        return None;
    }
    let policy = match common.text_flow {
        _ if top_and_bottom => FrameExclusionPolicy::BothSides,
        TextFlow::BothSides => FrameExclusionPolicy::BothSides,
        TextFlow::LargestOnly => FrameExclusionPolicy::LargestSide,
        TextFlow::LeftOnly => FrameExclusionPolicy::LeftSide,
        TextFlow::RightOnly => FrameExclusionPolicy::RightSide,
    };
    let full_width = top_and_bottom.then(|| column_horizontal.clone());
// ==== next ====
    let horizontal = visible_left.saturating_sub(i32::from(common.margin.left))
        ..visible_left
            .saturating_add(width)
            .saturating_add(i32::from(common.margin.right));
// ==== replace ====
    let horizontal = visible_left.saturating_sub(i32::from(common.margin.left))
        ..visible_left
            .saturating_add(width)
            .saturating_add(i32::from(common.margin.right));
    let horizontal = full_width.map_or(horizontal, |column| {
        column.start.saturating_sub(1)..column.end.saturating_add(1)
    });
