// ==== find ====
) -> Option<PictureBandLayout> {
    let host = paragraphs.get(host_index)?;
// ==== replace ====
) -> Option<PictureBandLayout> {
    claude_layout_picture_band_impl(paragraphs, host_index, column_width_px, styles, dpi, false)
}

/// [claude-hwpx load-picture-band] 열 때 합성 줄을 띠로 짤 때는 그림이 문서 끝 문단보다 아래로 걸쳐도 받는다
/// (한/글은 문서 끝 문단까지 띠에 둔다 — 한국문화 14단원 마지막 쪽). 편집 경로의 거절 사유(빈 문단 하나뿐인 문서)는
/// 저장 줄이 없는 문단에만 쓰는 열기 경로에서는 생기지 않는다.
pub(crate) fn claude_layout_picture_band_to_doc_end(
    paragraphs: &[Paragraph],
    host_index: usize,
    column_width_px: f64,
    styles: &ResolvedStyleSet,
    dpi: f64,
) -> Option<PictureBandLayout> {
    claude_layout_picture_band_impl(paragraphs, host_index, column_width_px, styles, dpi, true)
}

fn claude_layout_picture_band_impl(
    paragraphs: &[Paragraph],
    host_index: usize,
    column_width_px: f64,
    styles: &ResolvedStyleSet,
    dpi: f64,
    allow_doc_end: bool,
) -> Option<PictureBandLayout> {
    let host = paragraphs.get(host_index)?;
// ==== next ====
        input.line_segs.clear();
        let paragraph_lines = layout_paragraph_in_frame(&input, &mut frame, styles, dpi)?;
        line_segs.push(paragraph_lines);
    }

    // 띠가 호스트에 닿기 전에 끝나면(앞 문단만 걸친 경우도 호스트는 띠에 넣어야 한다) 호스트까지 이어진 경우만 받는다
    (!line_segs.is_empty()
        && band_start + line_segs.len() > host_index
        && (frame.top >= exclusion_end || ended_at_break))
        .then_some(PictureBandLayout {
// ==== replace ====
        input.line_segs.clear();
        // [claude-hwpx band-tac-table] 글 없이 글자처럼 취급 표 하나만 있는 문단도 띠에 둔다. 한/글은 그 줄을 띠 왼쪽에서
        // 시작하고 줄 높이를 표 높이(바깥 여백 포함)로 잡는다 — 표가 띠보다 넓으면 오른쪽으로 넘친다(한국문화 14단원
        // 한/글 재저장: 표 줄 horzpos 34627, 폭 13561, 높이 3164 = 표 2882 + 바깥 여백 282, 줄 간격은 글자 모양 기준 720).
        // 띠 틀은 표를 받지 않으므로 표를 뺀 빈 줄로 띠 자리를 잡고 줄 높이만 표 높이로 바꾼다
        let tac_table_only = (input.controls.len() == 1
            && !input.text.chars().any(|ch| ch > '\u{001F}' && ch != '\u{FFFC}' && !ch.is_whitespace()))
        .then(|| match &input.controls[0] {
            Control::Table(t) if t.common.treat_as_char => Some(
                (t.common.height as i32)
                    .saturating_add(i32::from(t.outer_margin_top))
                    .saturating_add(i32::from(t.outer_margin_bottom)),
            ),
            _ => None,
        })
        .flatten();
        let paragraph_lines = if let Some(table_h) = tac_table_only {
            let mut probe = input.clone();
            probe.controls.clear();
            probe.text.clear();
            probe.char_offsets.clear();
            let mut rows = layout_paragraph_in_frame(&probe, &mut frame, styles, dpi)?;
            let row = rows.first_mut()?;
            if table_h > row.line_height {
                frame.top = frame.top.saturating_add(table_h - row.line_height);
                row.line_height = table_h;
                row.text_height = table_h;
                row.baseline_distance = baseline_distance_hwp(table_h);
            }
            rows.truncate(1);
            rows
        } else {
            layout_paragraph_in_frame(&input, &mut frame, styles, dpi)?
        };
        line_segs.push(paragraph_lines);
    }

    // 띠가 호스트에 닿기 전에 끝나면(앞 문단만 걸친 경우도 호스트는 띠에 넣어야 한다) 호스트까지 이어진 경우만 받는다
    (!line_segs.is_empty()
        && band_start + line_segs.len() > host_index
        && (frame.top >= exclusion_end
            || ended_at_break
            || (allow_doc_end && band_start + line_segs.len() == paragraphs.len())))
        .then_some(PictureBandLayout {
