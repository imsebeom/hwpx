// ==== find ====
        // [claude-hwpx tac-restate-on-open] 한/글처럼 열 때
// ==== replace ====
        // [claude-hwpx cell-missing-line-gap] 칸 안 이웃 문단 사이 간격에서 문단 간격 설정을 뺀 나머지가 앞 문단 마지막 줄 분량의 정수배면 빠진 줄의 흔적이다
        // (에디터 저장본: 줄이 줄어든 뒤 뒤 문단 위치가 남음). 한/글은 열 때 닫는다(결과보고서 33쪽 가운데 칸 7.8px). 한/글 저장본의
        // 설명 안 되는 칸 간격(정답본 13곳)은 줄 분량의 정수배가 아니다. 개체가 든 문단은 건드리지 않는다
        if matches!(doc.source_format, crate::parser::FileFormat::Hwpx) {
            use crate::model::control::Control;
            fn claude_close_cell_gaps(
                t: &mut crate::model::table::Table,
                styles: &crate::renderer::style_resolver::ResolvedStyleSet,
                dpi: f64,
            ) {
                let plain = |p: &crate::model::paragraph::Paragraph| {
                    p.controls.iter().all(|c| {
                        !matches!(c, Control::Picture(_) | Control::Shape(_) | Control::Table(_) | Control::Equation(_))
                    })
                };
                let sp = |id: u16, after: bool| {
                    styles
                        .para_styles
                        .get(id as usize)
                        .map(|s| crate::renderer::px_to_hwpunit(if after { s.spacing_after } else { s.spacing_before }, dpi))
                        .unwrap_or(0)
                };
                for cell in &mut t.cells {
                    let mut shift = 0i32;
                    let n = cell.paragraphs.len();
                    for i in 0..n {
                        if shift != 0 {
                            for s in &mut cell.paragraphs[i].line_segs {
                                s.vertical_pos = s.vertical_pos.saturating_sub(shift);
                            }
                        }
                        if i + 1 >= n {
                            continue;
                        }
                        let (a, b) = (&cell.paragraphs[i], &cell.paragraphs[i + 1]);
                        if !plain(a) || !plain(b) {
                            continue;
                        }
                        let (Some(la), Some(fb)) = (a.line_segs.last(), b.line_segs.first()) else {
                            continue;
                        };
                        if la.tag & 0x8000_0000 != 0 || fb.tag & 0x8000_0000 != 0 {
                            continue;
                        }
                        let adv = la.line_height.saturating_add(la.line_spacing);
                        let gap = fb.vertical_pos.saturating_sub(shift)
                            - la.vertical_pos.saturating_add(adv)
                            - sp(a.para_shape_id, true)
                            - sp(b.para_shape_id, false);
                        if adv > 0 && gap >= adv - 4 {
                            let k = (gap + adv / 2) / adv;
                            if (gap - k * adv).abs() <= 4 {
                                shift = shift.saturating_add(gap);
                            }
                        }
                    }
                    for p in &mut cell.paragraphs {
                        for c in &mut p.controls {
                            if let Control::Table(nt) = c {
                                claude_close_cell_gaps(nt, styles, dpi);
                            }
                        }
                    }
                }
            }
            let dpi = doc.dpi;
            for sec in &mut doc.document.sections {
                for p in &mut sec.paragraphs {
                    for c in &mut p.controls {
                        if let Control::Table(t) = c {
                            claude_close_cell_gaps(t, &doc.styles, dpi);
                        }
                    }
                }
            }
        }
        // [claude-hwpx tac-restate-on-open] 한/글처럼 열 때
