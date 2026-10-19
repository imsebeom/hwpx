// ==== find ====
pub(crate) fn para_has_no_stored_line_segs(p: &crate::model::paragraph::Paragraph) -> bool {
    p.line_segs.is_empty() || p.line_segs.iter().all(|s| s.tag & 0x8000_0000 != 0)
}
// ==== replace ====
pub(crate) fn para_has_no_stored_line_segs(p: &crate::model::paragraph::Paragraph) -> bool {
    p.line_segs.is_empty() || p.line_segs.iter().all(|s| s.tag & 0x8000_0000 != 0)
}

/// [claude-hwpx full-square-empty] 줄 배치 없는 글 없는 문단에 어울림 표(문단 기준) 하나만 있고, 표 너비 + 바깥 여백 좌우가 줄 폭 이상(옆에 글 자리 없음)
pub(crate) fn claude_full_square_empty_host(
    p: &crate::model::paragraph::Paragraph,
    t: &crate::model::table::Table,
) -> bool {
    p.text.is_empty()
        && para_has_no_stored_line_segs(p)
        && !t.common.treat_as_char
        && matches!(t.common.text_wrap, crate::model::shape::TextWrap::Square)
        && matches!(t.common.vert_rel_to, crate::model::shape::VertRelTo::Para)
        && p
            .controls
            .iter()
            .filter(|c| {
                matches!(
                    c,
                    crate::model::control::Control::Table(_)
                        | crate::model::control::Control::Picture(_)
                        | crate::model::control::Control::Shape(_)
                )
            })
            .count()
            == 1
        && p.line_segs.first().is_some_and(|s| {
            s.segment_width > 0
                && t.common.width as i64 + t.outer_margin_left as i64 + t.outer_margin_right as i64
                    >= s.segment_width as i64
        })
}
