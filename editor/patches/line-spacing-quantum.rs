// ==== find ====
                (line_height_hwp as f64 * (ls_value - 100.0) / 100.0).round() as i32
// ==== replace ====
                // [claude-hwpx line-spacing-quantum] 한/글은 줄 간격도 4 HWPUNIT 단위로 반올림해 적는다
                // (9pt 130% 는 270 이 아니라 272, 11pt 130% 는 332 — 2026-10-06 한/글 재저장 줄 기록).
                // 음수(100% 미만)는 실측이 없어 종전대로 둔다.
                let spacing = line_height_hwp as f64 * (ls_value - 100.0) / 100.0;
                if spacing > 0.0 {
                    (spacing / 4.0 + 0.5 + 1e-6).floor() as i32 * 4
                } else {
                    spacing.round() as i32
                }
// ==== next ====
            let mut vpos = orig.as_ref().map(|ls| ls.vertical_pos).unwrap_or(0);
            for seg in &mut new_line_segs {
                seg.vertical_pos = vpos;
// ==== replace ====
            // 「줄 간격에 영향」이 켜진 글자처럼 취급 개체만 있는 줄은 줄 간격 % 를 글자 크기가 아니라 개체 높이에 건다.
            // 한/글 재저장 317개 문서: 꺼진 표, 그림 2,827건은 글자 크기 기준, 켜진 5건은 모두 개체 높이 기준.
            // 종전에는 이 속성을 읽기만 해, 107% 문단의 머리 표 아래가 한/글보다 520 HWPUNIT 좁아 뒤 내용이 당겨졌다.
            if matches!(ls_type, LineSpacingType::Percent)
                && orig_line_segs.is_empty()
                && para.controls.iter().any(|ctrl| match ctrl {
                    Control::Table(table) => {
                        table.common.treat_as_char && table.common.affect_line_spacing
                    }
                    Control::Picture(picture) => {
                        picture.common.treat_as_char && picture.common.affect_line_spacing
                    }
                    Control::Equation(equation) => {
                        equation.common.treat_as_char && equation.common.affect_line_spacing
                    }
                    Control::Shape(shape) => {
                        shape.common().treat_as_char && shape.common().affect_line_spacing
                    }
                    _ => false,
                })
            {
                for seg in &mut new_line_segs {
                    seg.line_spacing =
                        compute_line_spacing_hwp(ls_type, ls_value, seg.line_height, dpi);
                }
            }
            let mut vpos = orig.as_ref().map(|ls| ls.vertical_pos).unwrap_or(0);
            for seg in &mut new_line_segs {
                seg.vertical_pos = vpos;
