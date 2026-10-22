// ==== find ====
fn composed_footnote_content_height(footnote: &Footnote, dpi: f64) -> f64 {
// ==== replace ====
/// [claude-hwpx body-note-fit] 본문 문단 각주의 (표지가 든 줄, 조판한 각주 높이). HWPX 단일 단만
fn claude_body_note_lines(st: &TypesetState, para: &Paragraph, dpi: f64) -> Vec<(usize, f64)> {
    if !st.profile.hwpx_container() || st.col_count != 1 {
        return Vec::new();
    }
    para.controls
        .iter()
        .enumerate()
        .filter_map(|(ci, c)| match c {
            Control::Footnote(f) => Some((
                crate::renderer::layout::control_line_seg_index(para, ci).unwrap_or(0),
                composed_footnote_content_height(f, dpi),
            )),
            _ => None,
        })
        .collect()
}

/// [claude-hwpx body-note-fit] 줄 from..=to 에 든 표지의 각주를 이 쪽에 더하면 늘어나는 각주 영역 높이(구분선, 각주 사이 포함)
fn claude_body_note_extra(st: &TypesetState, notes: &[(usize, f64)], from: usize, to: usize) -> f64 {
    let (h, n) = notes
        .iter()
        .filter(|(l, _)| *l >= from && *l <= to)
        .fold((0.0, 0usize), |(h, n), (_, nh)| (h + nh, n + 1));
    if n == 0 {
        0.0
    } else {
        (st.projected_footnote_height(h, n) - st.current_footnote_height).max(0.0)
    }
}

fn composed_footnote_content_height(footnote: &Footnote, dpi: f64) -> f64 {
// ==== next ====
        if std::env::var("RHWP_DIAG_6031").is_ok()
            && st.current_height + page_end_fit_height > available
// ==== replace ====
        // [claude-hwpx body-note-fit] ① 문단을 통째로 담을 때 문단 안 각주까지 들어가야 한다(가이드북 파트2 합본 38쪽, 한/글 37쪽)
        let claude_note_lines = claude_body_note_lines(st, para, self.dpi);
        let claude_whole_note_h =
            claude_body_note_extra(st, &claude_note_lines, 0, fmt.line_heights.len().saturating_sub(1));
        if std::env::var("RHWP_DIAG_6031").is_ok()
            && st.current_height + page_end_fit_height > available
// ==== next ====
                let content_h = fmt.line_heights[li];
                if cumulative + content_h > avail_for_lines && li > cursor_line {
// ==== replace ====
                let content_h = fmt.line_heights[li];
                // [claude-hwpx body-note-fit] ② 이번 쪽 줄 범위에 든 표지의 각주까지 들어가야 그 줄을 담는다
                let claude_note_h = claude_body_note_extra(st, &claude_note_lines, cursor_line, li);
                if cumulative + content_h + claude_note_h > avail_for_lines && li > cursor_line {
// ==== next ====
        if (st.current_height >= available
            || remaining < first_line_h
            || (stored_whole_para_reset && !hangul2024_split_refit)
// ==== replace ====
        if (st.current_height >= available
            // [claude-hwpx body-note-fit] 첫 줄에 표지가 있으면 그 각주까지 들어가야 이 쪽에서 시작한다(파트2 합본 101쪽 각주 121)
            || remaining < first_line_h + claude_body_note_extra(st, &claude_note_lines, 0, 0)
            || (stored_whole_para_reset && !hangul2024_split_refit)
// ==== next ====
                            let routed = if whole_note_owned_by_tail_page {
                                None
                            } else {
                                match collision_routed {
                                    Some(route) => route,
                                    None => multi_note_routed,
                                }
                            };
// ==== replace ====
                            let routed = if whole_note_owned_by_tail_page {
                                None
                            } else {
                                match collision_routed {
                                    Some(route) => route,
                                    None => multi_note_routed,
                                }
                            };
                            // [claude-hwpx body-note-fit] ③ 쪽에 걸친 문단의 각주는 표지가 든 줄이 놓인 쪽에 둔다
                            let routed = routed.or_else(|| {
                                (st.profile.hwpx_container() && st.col_count == 1)
                                    .then(|| {
                                        crate::renderer::pagination::find_inline_control_target_page(
                                            &st.pages,
                                            &st.current_items,
                                            para_idx,
                                            ctrl_idx,
                                            para,
                                        )
                                    })
                                    .flatten()
                            });
// ==== next ====
            && (hangul2024_blank_spill
                || st.current_height + page_end_fit_height <= available
// ==== replace ====
            && (hangul2024_blank_spill
                || st.current_height + page_end_fit_height + claude_whole_note_h <= available
