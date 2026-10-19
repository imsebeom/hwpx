// ==== find ====
pub(crate) fn para_has_no_stored_line_segs(p: &crate::model::paragraph::Paragraph) -> bool {
    p.line_segs.is_empty() || p.line_segs.iter().all(|s| s.tag & 0x8000_0000 != 0)
}
// ==== replace ====
pub(crate) fn para_has_no_stored_line_segs(p: &crate::model::paragraph::Paragraph) -> bool {
    p.line_segs.is_empty() || p.line_segs.iter().all(|s| s.tag & 0x8000_0000 != 0)
}

/// [claude-hwpx multi-float-host-line] 줄 배치 없는 글 없는 문단에 자리 차지 표(문단 기준)만 둘 이상이면 (첫 표, 마지막 표, 호스트 줄 높이 + 줄 간격 HU).
/// 한/글은 이 호스트 줄을 그 쪽에 놓인 마지막 표 아래에 둔다(표 하나면 표 위, 폭 0 이라 높이를 쓰지 않는다).
pub(crate) fn claude_multi_float_host_line(
    p: &crate::model::paragraph::Paragraph,
) -> Option<(usize, usize, i32)> {
    if !p.text.is_empty() || !para_has_no_stored_line_segs(p) {
        return None;
    }
    let mut floats = Vec::new();
    for (i, c) in p.controls.iter().enumerate() {
        match c {
            crate::model::control::Control::Table(t)
                if !t.common.treat_as_char
                    && matches!(t.common.text_wrap, crate::model::shape::TextWrap::TopAndBottom)
                    && matches!(t.common.vert_rel_to, crate::model::shape::VertRelTo::Para) =>
            {
                floats.push(i)
            }
            crate::model::control::Control::Table(_)
            | crate::model::control::Control::Picture(_)
            | crate::model::control::Control::Shape(_) => return None,
            _ => {}
        }
    }
    if floats.len() < 2 {
        return None;
    }
    let seg = p.line_segs.first()?;
    let hu = seg.line_height + seg.line_spacing.max(0);
    (hu > 0).then(|| (floats[0], floats[floats.len() - 1], hu))
}
