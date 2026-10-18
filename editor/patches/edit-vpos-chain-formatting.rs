// ==== find ====
fn body_paragraph_box_for_para_shape(
// ==== replace ====
/// [claude-hwpx edit-vpos-chain] 줄을 모두 새로 만든 본문 문단들의 vpos 사슬을 문서 열기 경로(document.rs running_vpos, synth-vpos-spacing)처럼 잇는다:
/// 문단 사이 = 앞 문단 아래 간격 + 이 문단 위 간격(표만 담은 문단의 아래 간격은 뺀다), 위아래 배치 그림과 표는 줄 높이보다 크면
/// 그만큼 더한다. 줄이 없는 문단은 건너뛰고 아래 간격도 넘기지 않는다.
fn claude_rechain_vpos(paragraphs: &mut [crate::model::paragraph::Paragraph], styles: &ResolvedStyleSet, dpi: f64) {
    use crate::model::control::Control;
    use crate::model::shape::TextWrap;
    let hu = |px: f64| (px * 7200.0 / dpi).round() as i32;
    let mut running: i32 = 0;
    let mut prev_after: i32 = 0;
    for para in paragraphs.iter_mut() {
        if para.line_segs.is_empty() {
            prev_after = 0;
            continue;
        }
        let style = styles.para_styles.get(para.para_shape_id as usize);
        running += prev_after + hu(style.map(|s| s.spacing_before).unwrap_or(0.0));
        let mut v = running;
        for seg in para.line_segs.iter_mut() {
            seg.vertical_pos = v;
            let h = if seg.line_height > seg.text_height && seg.text_height > 0 { seg.text_height } else { seg.line_height };
            v += h + seg.line_spacing;
        }
        let seg_total: i32 = para.line_segs.iter().map(|s| s.line_height + s.line_spacing).sum();
        for ctrl in para.controls.iter() {
            let obj = match ctrl {
                Control::Picture(p)
                    if !p.common.treat_as_char && matches!(p.common.text_wrap, TextWrap::TopAndBottom) && p.common.height > 0 =>
                {
                    p.common.height as i32 + p.common.vertical_offset as i32
                }
                Control::Table(t)
                    if !t.common.treat_as_char && matches!(t.common.text_wrap, TextWrap::TopAndBottom) && t.common.height > 0 && t.raw_ctrl_data.is_empty() =>
                {
                    t.common.height as i32 + t.common.vertical_offset as i32 + t.outer_margin_top as i32 + t.outer_margin_bottom as i32
                }
                _ => continue,
            };
            if obj > seg_total {
                v += obj - seg_total;
            }
        }
        running = v;
        let table_only = para.text.trim().is_empty()
            && para.controls.iter().any(|c| {
                matches!(c, Control::Table(t) if !t.common.treat_as_char && matches!(t.common.text_wrap, TextWrap::TopAndBottom))
            });
        prev_after = if table_only { 0 } else { hu(style.map(|s| s.spacing_after).unwrap_or(0.0)) };
    }
}

fn body_paragraph_box_for_para_shape(
// ==== next ====
            para.line_segs.clear();
            reflow_line_segs(para, paragraph_box, &styles, dpi);
        }
    }
// ==== replace ====
            para.line_segs.clear();
            reflow_line_segs(para, paragraph_box, &styles, dpi);
        }
        // [claude-hwpx edit-vpos-chain] 줄을 모두 새로 만들었으니 문서 열기처럼 vpos 사슬을 잇는다(종전에는 문단마다 0)
        claude_rechain_vpos(&mut section.paragraphs, &styles, dpi);
    }
