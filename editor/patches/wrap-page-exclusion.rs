// ==== find ====
pub(crate) fn resolve_picture_exclusion(
// ==== replace ====
/// [claude-hwpx wrap-page-band] 편집 뒤 그림 띠가 쪽, 종이 기준 그림도 비키게 편집 쪽이 넘기는 쪽 기하.
/// 모두 HWPUNIT, 단 왼쪽 위가 0 인 좌표다. host_top 은 호스트 문단 첫 줄의 저장 vpos(단 윗변 기준)
#[derive(Clone, Copy, Debug)]
pub(crate) struct ClaudeBandPage {
    pub(crate) page_left: i32,
    pub(crate) page_width: i32,
    pub(crate) page_top: i32,
    pub(crate) paper_left: i32,
    pub(crate) paper_width: i32,
    pub(crate) paper_top: i32,
    pub(crate) host_top: i32,
}

thread_local! {
    /// 그림 띠 함수 서명을 바꾸지 않으려고 편집 쪽이 호출 직전에 넣고 직후에 비운다
    pub(crate) static CLAUDE_BAND_PAGE: std::cell::Cell<Option<ClaudeBandPage>> =
        const { std::cell::Cell::new(None) };
}

/// 쪽, 종이 기준 어울림/자리 차지 그림의 제외 영역(문단 좌표). `resolve_picture_exclusion` 이 받지 않는 경우만 본다
pub(crate) fn claude_page_picture_exclusion(
    picture: &Picture,
    column_horizontal: &Range<i32>,
    paragraph_horizontal: &Range<i32>,
    paragraph_top: i32,
) -> Option<FrameExclusion> {
    let page = CLAUDE_BAND_PAGE.with(|cell| cell.get())?;
    let common = &picture.common;
    let top_and_bottom = common.text_wrap == TextWrap::TopAndBottom;
    let page_based = matches!(common.vert_rel_to, VertRelTo::Page | VertRelTo::Paper)
        || matches!(common.horz_rel_to, HorzRelTo::Page | HorzRelTo::Paper);
    if common.treat_as_char
        || picture.caption.is_some()
        || !(common.text_wrap == TextWrap::Square || top_and_bottom)
        || !page_based
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
    let (width, height) = picture_flow_frame_size_hu(picture);
    if width <= 0 || height <= 0 {
        return None;
    }
    let reference = match common.horz_rel_to {
        HorzRelTo::Column => column_horizontal.clone(),
        HorzRelTo::Para => paragraph_horizontal.clone(),
        HorzRelTo::Page => page.page_left..page.page_left.saturating_add(page.page_width),
        HorzRelTo::Paper => page.paper_left..page.paper_left.saturating_add(page.paper_width),
    };
    let horizontal_offset = signed_hwpunit(common.horizontal_offset);
    let reference_width = reference.end.saturating_sub(reference.start);
    let visible_left = match common.horz_align {
        HorzAlign::Left | HorzAlign::Inside => reference.start.saturating_add(horizontal_offset),
        HorzAlign::Center => reference
            .start
            .saturating_add(reference_width.saturating_sub(width).max(0).saturating_div(2))
            .saturating_add(horizontal_offset),
        HorzAlign::Right | HorzAlign::Outside => reference
            .end
            .saturating_sub(width)
            .saturating_sub(horizontal_offset),
    };
    let vertical_offset = signed_hwpunit(common.vertical_offset);
    let visible_top = match common.vert_rel_to {
        VertRelTo::Page => page.page_top.saturating_sub(page.host_top),
        VertRelTo::Paper => page.paper_top.saturating_sub(page.host_top),
        VertRelTo::Para => paragraph_top,
    }
    .saturating_add(vertical_offset);
    let horizontal = if top_and_bottom {
        column_horizontal.start.saturating_sub(1)..column_horizontal.end.saturating_add(1)
    } else {
        visible_left.saturating_sub(i32::from(common.margin.left))
            ..visible_left
                .saturating_add(width)
                .saturating_add(i32::from(common.margin.right))
    };
    let vertical = visible_top.saturating_sub(i32::from(common.margin.top))
        ..visible_top
            .saturating_add(height)
            .saturating_add(i32::from(common.margin.bottom));
    (!horizontal.is_empty() && !vertical.is_empty()).then_some(FrameExclusion {
        horizontal,
        vertical,
        policy,
    })
}

pub(crate) fn resolve_picture_exclusion(
