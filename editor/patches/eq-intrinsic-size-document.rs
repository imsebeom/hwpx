// ==== find ====
        Self::reflow_zero_height_paragraphs(
// ==== replace ====
        // [claude-hwpx eq-intrinsic-size] 줄 배치 없는 문단(빌더, 도구 산출물)의 글자처럼 취급 수식은 스크립트로 잰 크기가 적힌 높이보다 크면 그 크기로
        // (빌더는 어림 크기를 적는다. 한/글은 그릴 때 다시 잰다). 줄 배치가 있는 문단은 한/글이 잰 줄 높이를 믿는다
        fn claude_fix_equation_sizes(paras: &mut [crate::model::paragraph::Paragraph]) {
            for p in paras.iter_mut() {
                let no_lines = p.line_segs.is_empty();
                for c in p.controls.iter_mut() {
                    match c {
                        crate::model::control::Control::Equation(eq) if no_lines && eq.common.treat_as_char && !eq.script.is_empty() => {
                            let (w, h) = crate::renderer::equation::intrinsic_size_hwp(&eq.script, eq.font_size);
                            if h > eq.common.height {
                                eq.common.height = h;
                                eq.common.width = w;
                            }
                        }
                        crate::model::control::Control::Table(t) => {
                            for cell in t.cells.iter_mut() {
                                claude_fix_equation_sizes(&mut cell.paragraphs);
                            }
                        }
                        _ => {}
                    }
                }
            }
        }
        for section in document.sections.iter_mut() {
            claude_fix_equation_sizes(&mut section.paragraphs);
        }
        Self::reflow_zero_height_paragraphs(
