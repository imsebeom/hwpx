// ==== find ====
    Some(advance + i32::from(bullet.width_adjust))
}

fn reflow_line_segs_impl(
// ==== replace ====
    Some(advance + i32::from(bullet.width_adjust))
}

/// [claude-hwpx number-head] 번호 문단 머리 정의의 원본 태그(raw_para_heads 에서 그 수준의 `<hh:paraHead ...>`).
fn claude_raw_para_head(raw: &str, level: usize) -> Option<&str> {
    let key = format!(" level=\"{}\"", level);
    let mut rest = raw;
    while let Some(i) = rest.find("paraHead ") {
        let tail = &rest[i..];
        let end = tail.find('>')?;
        if tail[..end].contains(&key) {
            return Some(&tail[..end]);
        }
        rest = &tail[end..];
    }
    None
}

/// [claude-hwpx number-head] 번호 문단에서 한/글이 번호에 내주는 자리(HWPUNIT)와 자동 내어쓰기 여부.
///
/// 한/글 2024 실측(test/conformance/lab e29): 자리 = 번호 글의 실제 폭 + 본문과의 거리(PERCENT 면 글자 크기 x %,
/// HWPUNIT 이면 그 값) + 너비 보정값. 번호 값은 시작 번호로 잰다(계수기는 그리는 단계에만 있다).
fn claude_number_head_hwp(para: &Paragraph, styles: &ResolvedStyleSet) -> Option<(i32, bool)> {
    let para_style = styles.para_styles.get(para.para_shape_id as usize)?;
    if para_style.head_type != crate::model::style::HeadType::Number {
        return None;
    }
    let numbering = styles
        .numberings
        .get((para_style.numbering_id as usize).checked_sub(1)?)?;
    let level = (para_style.para_level as usize).min(6);
    let format = &numbering.level_formats[level];
    if format.is_empty() {
        return None;
    }
    let head = numbering.heads[level];
    let (auto_indent, percent, inst_width) =
        match numbering.raw_para_heads.as_deref().and_then(|raw| claude_raw_para_head(raw, level + 1)) {
            Some(tag) => (
                !tag.contains("autoIndent=\"0\""),
                !tag.contains("textOffsetType=\"HWPUNIT\""),
                !tag.contains("useInstWidth=\"0\""),
            ),
            None => (head.attr & 0x08 != 0, head.attr & 0x10 == 0, head.attr & 0x04 != 0),
        };
    if !inst_width {
        return None;
    }
    let text = crate::renderer::layout::expand_numbering_format(
        format,
        &[1; 7],
        numbering,
        &numbering.level_start_numbers,
        level,
    );
    if text.is_empty() {
        return None;
    }
    let char_style_id = if (head.char_shape_id as usize) < styles.char_styles.len() {
        head.char_shape_id
    } else {
        para.char_shapes.first().map(|shape| shape.char_shape_id)?
    };
    let font_size = styles
        .char_styles
        .get(char_style_id as usize)
        .map(|style| style.font_size)
        .filter(|size| *size > 0.0)?;
    let width_px: f64 = text
        .chars()
        .map(|ch| {
            let ts = resolved_to_text_style(styles, char_style_id, detect_lang_category(ch));
            estimate_text_width_unrounded(&ch.to_string(), &ts)
        })
        .sum();
    // 1/1800 인치(HWPUNIT/4) 단위
    let quarter = 75.0 / 4.0;
    let advance = if percent {
        ((width_px + font_size * f64::from(head.text_distance) / 100.0) * quarter + 0.5 + 1e-6).floor() as i32 * 4
    } else {
        (width_px * quarter + 0.5 + 1e-6).floor() as i32 * 4 + i32::from(head.text_distance)
    };
    Some((advance + i32::from(head.width_adjust), auto_indent))
}

fn reflow_line_segs_impl(
// ==== next ====
        .filter(|advance| *advance > 0 && *advance < seg_width_hwp)
        .unwrap_or(0);
    let fill_box = if bullet_advance_hwp > 0 {
// ==== replace ====
        .filter(|advance| *advance > 0 && *advance < seg_width_hwp)
        .unwrap_or(0);
    // [claude-hwpx number-head] 번호 자리도 뺀다. 자동 내어쓰기면 글머리표처럼 모든 줄을 좁히고, 아니면 첫 줄만 좁히도록 들여쓰기를 고친다
    // (상자를 m 만큼 좁히고 들여쓰기로 나머지를 맞춘다: 첫 줄 = 폭 - max(들여쓰기, 0) - 자리, 이어지는 줄 = 폭 - max(-들여쓰기, 0))
    let mut claude_indent_override: Option<f64> = None;
    let bullet_advance_hwp = if bullet_advance_hwp > 0 {
        bullet_advance_hwp
    } else {
        match claude_number_head_hwp(para, styles).filter(|(advance, _)| *advance > 0 && *advance < seg_width_hwp) {
            Some((advance, true)) => advance,
            Some((advance, false)) => {
                let indent = styles.para_styles.get(para.para_shape_id as usize).map(|s| s.indent).unwrap_or(0.0);
                let advance_px = crate::renderer::hwpunit_to_px(advance, dpi);
                let shift_px = if indent >= 0.0 { 0.0 } else { advance_px.min(-indent) };
                claude_indent_override = Some(if indent >= 0.0 {
                    indent + advance_px
                } else if advance_px >= -indent {
                    advance_px + indent
                } else {
                    indent + advance_px
                });
                px_to_hwpunit(shift_px, dpi)
            }
            None => 0,
        }
    };
    let fill_box = if bullet_advance_hwp > 0 {
// ==== next ====
    let indent_px = para_style.map(|s| s.indent).unwrap_or(0.0);
// ==== replace ====
    // [claude-hwpx number-head] 번호 자리가 첫 줄만 좁히면 고친 들여쓰기
    let indent_px = claude_indent_override.unwrap_or_else(|| para_style.map(|s| s.indent).unwrap_or(0.0));
// ==== next ====
        if let Some(mut projected) = layout_paragraph_in_frame(para, &mut frame, styles, dpi) {
// ==== replace ====
        if let Some(mut projected) =
            // [claude-hwpx number-head]
            layout_paragraph_in_frame_indent(para, &mut frame, styles, dpi, claude_indent_override)
        {
// ==== next ====
    layout_paragraph_in_frame_impl(para, frame, styles, dpi, true)
}

fn layout_paragraph_in_frame_impl(
    para: &Paragraph,
    frame: &mut LayoutFrame,
    styles: &ResolvedStyleSet,
    dpi: f64,
    allow_kerning: bool,
) -> Option<Vec<LineSeg>> {
// ==== replace ====
    layout_paragraph_in_frame_impl(para, frame, styles, dpi, true, None)
}

/// [claude-hwpx number-head] 들여쓰기를 문단 모양 대신 주어진 값으로 쓰는 판(번호 자리가 첫 줄만 좁힐 때).
fn layout_paragraph_in_frame_indent(
    para: &Paragraph,
    frame: &mut LayoutFrame,
    styles: &ResolvedStyleSet,
    dpi: f64,
    indent_override: Option<f64>,
) -> Option<Vec<LineSeg>> {
    layout_paragraph_in_frame_impl(para, frame, styles, dpi, true, indent_override)
}

fn layout_paragraph_in_frame_impl(
    para: &Paragraph,
    frame: &mut LayoutFrame,
    styles: &ResolvedStyleSet,
    dpi: f64,
    allow_kerning: bool,
    indent_override: Option<f64>,
) -> Option<Vec<LineSeg>> {
// ==== next ====
    let indent_px = para_style.map(|style| style.indent).unwrap_or(0.0);
// ==== replace ====
    let indent_px = indent_override.unwrap_or_else(|| para_style.map(|style| style.indent).unwrap_or(0.0));
// ==== next ====
        return layout_paragraph_in_frame_impl(para, frame, styles, dpi, false);
// ==== replace ====
        return layout_paragraph_in_frame_impl(para, frame, styles, dpi, false, indent_override);
