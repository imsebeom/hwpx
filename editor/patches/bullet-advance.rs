// ==== find ====
fn reflow_line_segs_impl(
    para: &mut Paragraph,
// ==== replace ====
/// [claude-hwpx bullet-advance] 글머리표 문단에서 한/글이 표식에 내주는 자리(HWPUNIT).
///
/// 한/글 2024 사다리 실측(2026-10-06, 9~13pt, 글머리 문자 6종, 본문과의 거리 0~100%, 너비 보정, 자동 내어쓰기 켬/끔):
/// 자리 = 반올림(글머리 칸 + 글자 크기 x 본문과의 거리 %) + 너비 보정값. 글머리 칸은 글꼴의 실제 글자 폭이 아니라
/// 전각이면 글자 크기, ASCII 반각이면 그 절반이다. 자동 내어쓰기가 켜져 있으면 이어지는 줄도 같은 만큼 좁다.
/// 종전 줄 나눔은 표식이 없는 것처럼 줄을 채워 한/글보다 두세 글자씩 더 담았다(그리는 쪽만 표식 폭을 뺐다).
///
/// 자동 내어쓰기가 꺼진 글머리표(첫 줄만 좁음), 그림 글머리표, 번호 문단은 다루지 않는다(None).
fn claude_bullet_advance_hwp(para: &Paragraph, styles: &ResolvedStyleSet) -> Option<i32> {
    let para_style = styles.para_styles.get(para.para_shape_id as usize)?;
    if para_style.head_type != crate::model::style::HeadType::Bullet {
        return None;
    }
    let bullet = styles
        .bullets
        .get((para_style.numbering_id as usize).checked_sub(1)?)?;
    if bullet.bullet_char == '\u{FFFF}' {
        return None;
    }
    let (auto_indent, percent) = match bullet.raw_para_head.as_deref() {
        Some(raw) => (
            !raw.contains("autoIndent=\"0\""),
            !raw.contains("textOffsetType=\"HWPUNIT\""),
        ),
        None => (bullet.attr & 0x08 != 0, bullet.attr & 0x10 == 0),
    };
    if !auto_indent {
        return None;
    }
    let char_style_id = if (bullet.char_shape_id as usize) < styles.char_styles.len() {
        bullet.char_shape_id
    } else {
        para.char_shapes.first().map(|shape| shape.char_shape_id)?
    };
    let font_size = styles
        .char_styles
        .get(char_style_id as usize)
        .map(|style| style.font_size)
        .filter(|size| *size > 0.0)?;
    // 1/1800 인치(HWPUNIT/4) 단위
    let em = font_size * 75.0 / 4.0;
    let cell = if (bullet.bullet_char as u32) < 0x80 {
        em / 2.0
    } else {
        em
    };
    let advance = if percent {
        (cell + em * f64::from(bullet.text_distance) / 100.0 + 0.5 + 1e-6).floor() as i32 * 4
    } else {
        (cell + 0.5 + 1e-6).floor() as i32 * 4 + i32::from(bullet.text_distance)
    };
    Some(advance + i32::from(bullet.width_adjust))
}

fn reflow_line_segs_impl(
    para: &mut Paragraph,
// ==== next ====
    let available_width_px = paragraph_box.width_px(dpi);

    // ParaPr의 줄간격 설정 (합성 LineSeg에서 line_spacing 계산에 사용)
// ==== replace ====
    // 글머리표 자리만큼 좁힌 상자에서 줄을 채운다. 저장하는 줄 기록(column_start, segment_width)은 한/글처럼 원래 상자다.
    let bullet_advance_hwp = claude_bullet_advance_hwp(para, styles)
        .filter(|advance| *advance > 0 && *advance < seg_width_hwp)
        .unwrap_or(0);
    let fill_box = if bullet_advance_hwp > 0 {
        ParagraphBox::content(
            published_horizontal.start + bullet_advance_hwp..published_horizontal.end,
        )
    } else {
        paragraph_box.clone()
    };
    let available_width_px = fill_box.width_px(dpi);

    // ParaPr의 줄간격 설정 (합성 LineSeg에서 line_spacing 계산에 사용)
// ==== next ====
        let mut frame =
            paragraph_box.frame(orig.as_ref().map(|line| line.vertical_pos).unwrap_or(0));
        if let Some(projected) = layout_paragraph_in_frame(para, &mut frame, styles, dpi) {
            para.replace_line_segs(projected);
            return false;
        }
// ==== replace ====
        let mut frame = fill_box.frame(orig.as_ref().map(|line| line.vertical_pos).unwrap_or(0));
        if let Some(mut projected) = layout_paragraph_in_frame(para, &mut frame, styles, dpi) {
            if bullet_advance_hwp > 0 {
                for seg in &mut projected {
                    seg.column_start = published_horizontal.start;
                    seg.segment_width = seg_width_hwp;
                }
            }
            para.replace_line_segs(projected);
            return false;
        }
