"""개발용: 어울림 도형(차트, OLE 등)도 띠(layout_picture_band)로 비켜, 다음 문단들이 도형이 남긴 빈 자리로 흐르게 한다.

    python apply_shape_band.py [--revert]

한/글 사본 실험(exp/make_squarepair.py, d268 둘째 구역 p31): 반 폭 차트 하나면 p32~p36 줄이 오른쪽 빈 자리(horzpos 23452, 폭 24736)로,
두 차트 사이 틈이 있으면 그 틈으로 흐른다. 엔진의 띠는 문단에 그림이 하나일 때만 받고(도형, 여럿은 None), 띠 안 문단에 위아래 간격이
있으면 거절해 차트 위에 글이 겹쳤다. 어울림 도형이 든 문단에서만(그림만 든 문단은 종전대로):
- 도형과 그림 모두를 각자의 앵커 줄 기준 제외 영역 여럿으로 둔다(frame_with 는 여럿을 받는다).
- 띠 안 문단의 위아래 간격을 띠 안에서 센다(종전에는 간격이 있으면 띠를 버렸다).
- 열 때 띠를 거는 문단 판정에 어울림 도형을 더한다.
자리가 없는 무리는 square-block 이 먼저 자리 차지로 바꾸므로 여기 오지 않는다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx shape-band]"
LB = "renderer/composer/line_breaking.rs"
DOC = "document_core/commands/document.rs"

EDITS = [
    (
        LB,
        """            Control::Picture(picture) if !picture.common.treat_as_char => {
                non_tac_pictures += 1;
            }
            Control::Equation(equation) if equation.common.treat_as_char => {}
""",
        f"""            Control::Picture(picture) if !picture.common.treat_as_char => {{
                non_tac_pictures += 1;
            }}
            // {TAG} 글자처럼 취급하지 않는 어울림 도형도 글 폭을 쓰지 않는다(띠가 제외 영역으로 비킨다)
            Control::Shape(shape)
                if !shape.common().treat_as_char
                    && shape.common().text_wrap == crate::model::shape::TextWrap::Square => {{}}
            Control::Equation(equation) if equation.common.treat_as_char => {{}}
""",
    ),
    (
        LB,
        """    let mut host_pictures = host
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
""",
        f"""    // {TAG} 어울림 도형(차트, OLE 등)이 든 문단은 도형과 그림 모두를 제외 영역 여럿으로 비킨다(한/글: 빈 자리마다 흐름)
    let claude_is_square_shape = |control: &Control| {{
        matches!(control, Control::Shape(s)
            if !s.common().treat_as_char
                && s.common().text_wrap == crate::model::shape::TextWrap::Square)
    }};
    let claude_shape_floats: Vec<(usize, crate::model::image::Picture)> =
        if host.controls.iter().any(|c| claude_is_square_shape(c)) {{
            host.controls
                .iter()
                .enumerate()
                .filter_map(|(index, control)| match control {{
                    Control::Picture(p) if !p.common.treat_as_char => Some((index, (**p).clone())),
                    Control::Shape(s)
                        if !s.common().treat_as_char
                            && matches!(
                                s.common().text_wrap,
                                crate::model::shape::TextWrap::Square
                                    | crate::model::shape::TextWrap::TopAndBottom
                            ) =>
                    {{
                        Some((
                            index,
                            crate::model::image::Picture {{
                                common: s.common().clone(),
                                ..Default::default()
                            }},
                        ))
                    }}
                    _ => None,
                }})
                .collect()
        }} else {{
            Vec::new()
        }};
    let claude_shape_band = !claude_shape_floats.is_empty();
    let mut host_pictures = host
        .controls
        .iter()
        .enumerate()
        .filter_map(|(index, control)| match control {{
            Control::Picture(picture) if !picture.common.treat_as_char => {{
                Some((index, picture.as_ref()))
            }}
            _ => None,
        }});
    let claude_first_picture = host_pictures.next();
    if !claude_shape_band && (claude_first_picture.is_none() || host_pictures.next().is_some()) {{
        return None;
    }}
    let (picture_control_index, picture) = match claude_first_picture {{
        Some(first) if !claude_shape_band => first,
        _ => {{
            let (index, float) = &claude_shape_floats[0];
            (*index, float)
        }}
    }};
""",
    ),
    (
        LB,
        """    let exclusion_end = exclusion.vertical.end;
    let mut frame = host_box.frame_with(0, vec![exclusion]);
""",
        f"""    // {TAG} 나머지 개체도 각자의 앵커 줄 기준으로 제외 영역을 더한다
    let mut claude_extra: Vec<crate::renderer::layout_frame::FrameExclusion> = Vec::new();
    if claude_shape_band {{
        let positions = host.control_utf16_positions();
        for (index, float) in claude_shape_floats.iter().skip(1) {{
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
        }}
    }}
    let exclusion_end = claude_extra
        .iter()
        .map(|e| e.vertical.end)
        .fold(exclusion.vertical.end, i32::max);
    let mut claude_all = vec![exclusion];
    claude_all.extend(claude_extra);
    let mut frame = host_box.frame_with(0, claude_all);
""",
    ),
    (
        LB,
        """            || paragraph_style.is_some_and(|style| {
                style.spacing_before.abs() > f64::EPSILON
                    || style.spacing_after.abs() > f64::EPSILON
                    || (style.page_break_before && !starts_band)
            })
""",
        f"""            || paragraph_style.is_some_and(|style| {{
                // {TAG} 도형 띠는 위아래 간격을 띠 안에서 센다(아래)
                (!claude_shape_band
                    && (style.spacing_before.abs() > f64::EPSILON
                        || style.spacing_after.abs() > f64::EPSILON))
                    || (style.page_break_before && !starts_band)
            }})
""",
    ),
    (
        LB,
        """        let mut input = paragraph.clone();
        // A picture-band projection is freshly computed implementation state,
""",
        f"""        // {TAG} 도형 띠: 문단 위 간격
        if claude_shape_band {{
            let before = paragraph_style.map(|s| px_to_hwpunit(s.spacing_before, dpi)).unwrap_or(0);
            frame.top = frame.top.saturating_add(before);
        }}
        let mut input = paragraph.clone();
        // A picture-band projection is freshly computed implementation state,
""",
    ),
    (
        LB,
        """        line_segs.push(paragraph_lines);
    }

    // 띠가 호스트에 닿기 전에 끝나면""",
        f"""        line_segs.push(paragraph_lines);
        // {TAG} 도형 띠: 문단 아래 간격
        if claude_shape_band {{
            let after = paragraph_style.map(|s| px_to_hwpunit(s.spacing_after, dpi)).unwrap_or(0);
            frame.top = frame.top.saturating_add(after);
        }}
    }}

    // 띠가 호스트에 닿기 전에 끝나면""",
    ),
    (
        DOC,
        """                    let is_host = section.paragraphs[hi].controls.iter().any(|c| {
                        matches!(c, Control::Picture(p)
                            if !p.common.treat_as_char
                                && p.common.text_wrap == crate::model::shape::TextWrap::Square)
                    });
""",
        f"""                    let is_host = section.paragraphs[hi].controls.iter().any(|c| {{
                        matches!(c, Control::Picture(p)
                            if !p.common.treat_as_char
                                && p.common.text_wrap == crate::model::shape::TextWrap::Square)
                            // {TAG} 어울림 도형(차트, OLE 등)도
                            || matches!(c, Control::Shape(s)
                                if !s.common().treat_as_char
                                    && s.common().text_wrap == crate::model::shape::TextWrap::Square)
                    }});
""",
    ),
]


def main():
    revert = "--revert" in sys.argv
    edits = list(reversed(EDITS)) if revert else EDITS
    for rel, find, repl in edits:
        if revert:
            find, repl = repl, find
        f = SRC / rel
        raw = f.read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in raw else "\n"
        s = raw.replace("\r\n", "\n")
        if (find not in s) if revert else (repl in s):
            print("이미", rel)
            continue
        n = s.count(find)
        if n != 1:
            sys.exit(f"{rel}: 자리 {n}곳 — {find[:60]!r}")
        s = s.replace(find, repl)
        f.write_bytes(s.replace("\n", nl).encode("utf-8"))
        print("넣음", rel)


if __name__ == "__main__":
    main()
