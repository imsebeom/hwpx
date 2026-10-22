// ==== find ====
                if outer.cell_index == 0 {
                    let is_shape = self
                        .document
                        .sections
                        .get(run.section_index)
                        .and_then(|s| s.paragraphs.get(ctx.parent_para_index))
                        .and_then(|p| p.controls.get(outer.control_index))
                        .map(|c| matches!(c, Control::Shape(_)))
                        .unwrap_or(false);
                    run.is_textbox = is_shape;
                } else {
                    run.is_textbox = false;
                }
// ==== replace ====
                // [claude-hwpx group-textbox] 도형이면 칸 번호(묶음 자식 경로)와 상관없이 글상자다(표 칸은 개체가 표라 false)
                run.is_textbox = self
                    .document
                    .sections
                    .get(run.section_index)
                    .and_then(|s| s.paragraphs.get(ctx.parent_para_index))
                    .and_then(|p| p.controls.get(outer.control_index))
                    .map(|c| matches!(c, Control::Shape(_)))
                    .unwrap_or(false);
