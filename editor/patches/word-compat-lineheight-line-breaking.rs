// ==== find ====
fn apply_inline_control_line_height(seg: &mut LineSeg, height_hwp: i32) {
// ==== replace ====
/// [claude-hwpx word-compat-lineheight] Word 호환 문서(targetProgram=MS_WORD + adjustLineheightToFont)의 줄 치수(HWPUNIT).
/// 한/글은 글꼴 파일의 hhea 줄 높이로 줄을 만든다(lab harvest_wordcompat.py, d076, d133):
/// 줄 높이 = 크기 x (ascender + descender + lineGap) / em x 1.3, 기준선 = ascender x 크기 + (줄 높이 - hhea 높이) / 2.
/// 문단 끝 빈 run 이 글보다 크면 줄 높이는 「빈 run 줄 높이 + 글 아랫부분」, 기준선은 빈 run 의 것이다
/// (harvest_wordmix.py, d133 126줄: 9pt 글 + 10pt 빈 run → 2126/1288). 그 줄의 비율 간격은 빈 run 줄 높이에 건다
/// (d133 10pt 글 + 12pt 빈 run 160% → 2517 에 간격 1244 = 2076 기준). 반환 (줄 높이, 기준선, 간격 기준 높이).
/// 글꼴 세로 수치가 없으면 None(종전대로).
fn claude_word_line_metrics(
    para: &Paragraph,
    styles: &ResolvedStyleSet,
    start_u16: u32,
    end_u16: u32,
    last_line: bool,
    dpi: f64,
) -> Option<(i32, i32, i32)> {
    if !styles.char_styles.first().is_some_and(|style| style.claude_word_compat) {
        return None;
    }
    let metric = |id: u32| -> Option<(f64, f64)> {
        let style = styles.char_styles.get(id as usize)?;
        let [asc, desc, gap] = crate::renderer::font_metrics_data::claude_font_vm(&style.font_family)?;
        let size = style.font_size * 7_200.0 / dpi;
        let ratio = asc + desc + gap;
        let lh = size * ratio * 1.3;
        Some((lh.round(), (asc * size + (lh - ratio * size) / 2.0).round()))
    };
    let refs = &para.char_shapes;
    if para.text.is_empty() {
        let (lh, bl) = metric(refs.first().map_or(0, |r| r.char_shape_id))?;
        return Some((lh as i32, bl as i32, lh as i32));
    }
    let text_end = char_index_to_utf16_offset(para, para.text.chars().count());
    let mut text: Option<(f64, f64)> = None;
    for (i, r) in refs.iter().enumerate() {
        let next = refs.get(i + 1).map_or(u32::MAX, |n| n.start_pos);
        if r.start_pos < text_end && next > r.start_pos && r.start_pos < end_u16 && next > start_u16 {
            let m = metric(r.char_shape_id)?;
            text = Some(match text {
                Some(t) if t.0 >= m.0 => t,
                _ => m,
            });
        }
    }
    let text = text?;
    let mark = refs
        .last()
        .filter(|r| last_line && r.start_pos >= text_end)
        .and_then(|r| metric(r.char_shape_id));
    let (lh, bl, base) = match mark {
        Some(m) if m.0 > text.0 => (m.0 + text.0 - text.1, m.1, m.0),
        _ => (text.0, text.1, text.0),
    };
    Some((lh as i32, bl as i32, base as i32))
}

fn apply_inline_control_line_height(seg: &mut LineSeg, height_hwp: i32) {
// ==== next ====
        let mut text_seg = make_line_seg(utf16_start, fs);
// ==== replace ====
        let mut text_seg = make_line_seg(utf16_start, fs);
        // [claude-hwpx word-compat-lineheight] Word 호환 문서의 비율 간격 줄은 글꼴 세로 수치로
        if matches!(ls_type, LineSpacingType::Percent) {
            let last_line = lb.end_idx >= text_len;
            let end_u16 = if last_line {
                char_index_to_utf16_offset(para, text_len)
            } else {
                claude_line_start_utf16(para, lb.end_idx)
            };
            if let Some((lh, bl, base)) = claude_word_line_metrics(para, styles, utf16_start, end_u16, last_line, dpi) {
                text_seg.line_height = lh;
                text_seg.text_height = lh;
                text_seg.baseline_distance = bl;
                text_seg.line_spacing = compute_line_spacing_hwp(ls_type, ls_value, base, dpi);
            }
        }
// ==== next ====
                let mut metrics = frame_metrics_for_line(
                    maximum_font_size,
                    fallback_font_size,
                    line_spacing_type,
                    line_spacing_value,
                    dpi,
                );
// ==== replace ====
                let mut metrics = frame_metrics_for_line(
                    maximum_font_size,
                    fallback_font_size,
                    line_spacing_type,
                    line_spacing_value,
                    dpi,
                );
                // [claude-hwpx word-compat-lineheight] 본문 줄 대부분이 이 경로다(줄 배치 없는 HWPX)
                if matches!(line_spacing_type, LineSpacingType::Percent) {
                    let span = segments.first().zip(segments.last()).map(|(a, b)| (a.text_range.start, b.text_range.end));
                    let (start_u16, end_u16) = span.unwrap_or((0, 0));
                    if let Some((lh, bl, base)) =
                        claude_word_line_metrics(para, styles, start_u16, end_u16, cursor.finished, dpi)
                    {
                        metrics.line_height = lh;
                        metrics.text_height = lh;
                        metrics.baseline_distance = bl;
                        metrics.line_spacing = compute_line_spacing_hwp(line_spacing_type, line_spacing_value, base, dpi);
                    }
                }
// ==== next ====
            let mut seg = make_line_seg(0, font_size);
            if let Some(template) = orig.as_ref() {
// ==== replace ====
            let mut seg = make_line_seg(0, font_size);
            // [claude-hwpx word-compat-lineheight] 빈 문단도 Word 호환 문서면 글꼴 세로 수치로
            if matches!(ls_type, LineSpacingType::Percent) {
                if let Some((lh, bl, base)) = claude_word_line_metrics(para, styles, 0, 0, true, dpi) {
                    seg.line_height = lh;
                    seg.text_height = lh;
                    seg.baseline_distance = bl;
                    seg.line_spacing = compute_line_spacing_hwp(ls_type, ls_value, base, dpi);
                }
            }
            if let Some(template) = orig.as_ref() {
