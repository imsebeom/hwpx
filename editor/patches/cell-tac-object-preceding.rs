// ==== find ====
                    .any(|line| line.runs.iter().any(|run| !run.text.trim().is_empty()));
                if has_visible_text {
                    has_preceding_text = true;
// ==== replace ====
                    .any(|line| line.runs.iter().any(|run| !run.text.trim().is_empty()));
                // [claude-hwpx cell-tac-object-preceding] 글자처럼 취급 개체(그림, 수식, 도형)만 든 문단도 줄을 차지한다.
                // 글만 세면 그 뒤 문단의 위아래 배치 표가 칸 맨 위(inner_area.y)로 올라가 그림과 겹쳤다(2026-10-07 표 속 표 끌기)
                let has_inline_object = para.controls.iter().any(|ctrl| match ctrl {
                    Control::Picture(pic) => pic.common.treat_as_char,
                    Control::Shape(shape) => shape.common().treat_as_char,
                    Control::Equation(_) => true,
                    _ => false,
                });
                if has_visible_text || has_inline_object {
                    has_preceding_text = true;
