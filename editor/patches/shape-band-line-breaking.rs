// ==== find ====
            Control::Picture(picture) if !picture.common.treat_as_char => {
                non_tac_pictures += 1;
            }
            Control::Equation(equation) if equation.common.treat_as_char => {}
// ==== replace ====
            Control::Picture(picture) if !picture.common.treat_as_char => {
                non_tac_pictures += 1;
            }
            // [claude-hwpx shape-band] 글자처럼 취급하지 않는 어울림 도형도 글 폭을 쓰지 않는다(띠가 제외 영역으로 비킨다)
            Control::Shape(shape)
                if !shape.common().treat_as_char
                    && shape.common().text_wrap == crate::model::shape::TextWrap::Square => {}
            Control::Equation(equation) if equation.common.treat_as_char => {}
// ==== next ====
    let mut host_pictures = host
        .controls
        .iter()
        .enumerate()
        .filter_map(|(index, control)| match control {
            Control::Picture(picture) if !picture.common.treat_as_char => {
                Some((index, picture.as_ref()))
            }
            _ => None,
        });
    let (picture_control_index, picture) = host_pictures.next()?;
    if host_pictures.next().is_some() {
        return None;
    }
// ==== replace ====
    // [claude-hwpx shape-band] 어울림 도형(차트, OLE 등)이 든 문단은 도형과 그림 모두를 제외 영역 여럿으로 비킨다(한/글: 빈 자리마다 흐름)
    let claude_is_square_shape = |control: &Control| {
        matches!(control, Control::Shape(s)
            if !s.common().treat_as_char
                && s.common().text_wrap == crate::model::shape::TextWrap::Square)
    };
    let claude_shape_floats: Vec<(usize, crate::model::image::Picture)> =
        if host.controls.iter().any(|c| claude_is_square_shape(c)) {
            host.controls
                .iter()
                .enumerate()
                .filter_map(|(index, control)| match control {
                    Control::Picture(p) if !p.common.treat_as_char => Some((index, (**p).clone())),
                    Control::Shape(s)
                        if !s.common().treat_as_char
                            && matches!(
                                s.common().text_wrap,
                                crate::model::shape::TextWrap::Square
                                    | crate::model::shape::TextWrap::TopAndBottom
                            ) =>
                    {
                        Some((
                            index,
                            crate::model::image::Picture {
                                common: s.common().clone(),
                                ..Default::default()
                            },
                        ))
                    }
                    _ => None,
                })
                .collect()
        } else {
            Vec::new()
        };
    let claude_shape_band = !claude_shape_floats.is_empty();
    let mut host_pictures = host
        .controls
        .iter()
        .enumerate()
        .filter_map(|(index, control)| match control {
            Control::Picture(picture) if !picture.common.treat_as_char => {
                Some((index, picture.as_ref()))
            }
            _ => None,
        });
    let claude_first_picture = host_pictures.next();
    if !claude_shape_band && (claude_first_picture.is_none() || host_pictures.next().is_some()) {
        return None;
    }
    let (picture_control_index, picture) = match claude_first_picture {
        Some(first) if !claude_shape_band => first,
        _ => {
            let (index, float) = &claude_shape_floats[0];
            (*index, float)
        }
    };
// ==== next ====
    let exclusion_end = exclusion.vertical.end;
    let mut frame = host_box.frame_with(0, vec![exclusion]);
// ==== replace ====
    // [claude-hwpx shape-band] 나머지 개체도 각자의 앵커 줄 기준으로 제외 영역을 더한다
    let mut claude_extra: Vec<crate::renderer::layout_frame::FrameExclusion> = Vec::new();
    if claude_shape_band {
        let positions = host.control_utf16_positions();
        for (index, float) in claude_shape_floats.iter().skip(1) {
            let raw = positions.get(*index).copied()?;
            let top = anchor_rows
                .iter()
                .rfind(|row| row.text_start <= raw)
                .map(|row| row.vertical_pos)?;
            claude_extra.push(crate::renderer::float_placement::resolve_picture_exclusion(
                float,
                column_horizontal.clone(),
                host_paragraph_horizontal.clone(),
                top,
            )?);
        }
    }
    let exclusion_end = claude_extra
        .iter()
        .map(|e| e.vertical.end)
        .fold(exclusion.vertical.end, i32::max);
    let mut claude_all = vec![exclusion];
    claude_all.extend(claude_extra);
    let mut frame = host_box.frame_with(0, claude_all);
// ==== next ====
            || paragraph_style.is_some_and(|style| {
                style.spacing_before.abs() > f64::EPSILON
                    || style.spacing_after.abs() > f64::EPSILON
                    || (style.page_break_before && !starts_band)
            })
// ==== replace ====
            || paragraph_style.is_some_and(|style| {
                // [claude-hwpx shape-band] 도형 띠는 위아래 간격을 띠 안에서 센다(아래)
                (!claude_shape_band
                    && (style.spacing_before.abs() > f64::EPSILON
                        || style.spacing_after.abs() > f64::EPSILON))
                    || (style.page_break_before && !starts_band)
            })
// ==== next ====
        let mut input = paragraph.clone();
        // A picture-band projection is freshly computed implementation state,
// ==== replace ====
        // [claude-hwpx shape-band] 도형 띠: 문단 위 간격
        if claude_shape_band {
            let before = paragraph_style.map(|s| px_to_hwpunit(s.spacing_before, dpi)).unwrap_or(0);
            frame.top = frame.top.saturating_add(before);
        }
        let mut input = paragraph.clone();
        // A picture-band projection is freshly computed implementation state,
// ==== next ====
        line_segs.push(paragraph_lines);
    }

    // 띠가 호스트에 닿기 전에 끝나면
// ==== replace ====
        line_segs.push(paragraph_lines);
        // [claude-hwpx shape-band] 도형 띠: 문단 아래 간격
        if claude_shape_band {
            let after = paragraph_style.map(|s| px_to_hwpunit(s.spacing_after, dpi)).unwrap_or(0);
            frame.top = frame.top.saturating_add(after);
        }
    }

    // 띠가 호스트에 닿기 전에 끝나면
