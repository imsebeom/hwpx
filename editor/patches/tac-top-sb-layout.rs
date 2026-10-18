// ==== find ====
                        if !is_column_top {
                            let spacing_before = styles
                                .para_styles
                                .get(ps_id)
                                .map(|ps| ps.spacing_before)
                                .unwrap_or(0.0);
                            if spacing_before > 0.0 {
                                y_offset += spacing_before;
                            }
                        }
                        if outer_margin_top_px > 0.0 {
// ==== replace ====
                        if !is_column_top {
                            let spacing_before = styles
                                .para_styles
                                .get(ps_id)
                                .map(|ps| ps.spacing_before)
                                .unwrap_or(0.0);
                            if spacing_before > 0.0 {
                                y_offset += spacing_before;
                            }
                        } else if self.profile.get().hwpx_container() {
                            // [claude-hwpx tac-top-sb] 쪽 머리 글자처럼 취급 표도 본문 문단의 쪽 머리 규칙대로 위 간격을 그린다(d218 쪽마다 −4.0pt)
                            let sb = styles
                                .para_styles
                                .get(ps_id)
                                .map(|ps| ps.spacing_before.max(0.0))
                                .unwrap_or(0.0);
                            if let Some(seg) = para.line_segs.first() {
                                let v = hwpunit_to_px(seg.vertical_pos.max(0), self.dpi);
                                let synth = seg.tag
                                    & crate::model::paragraph::LineSeg::TAG_IMPLEMENTATION_PROPERTY
                                    != 0;
                                let add = if para_index == 0 {
                                    sb.min(v)
                                } else if !synth && v <= sb + 0.5 {
                                    v
                                } else {
                                    sb
                                };
                                if sb > 0.0 && add > 0.0 {
                                    y_offset += add;
                                }
                            }
                        }
                        if outer_margin_top_px > 0.0 {
// ==== next ====
                PageItem::Table { para_index, .. } => paragraphs
                    .get(*para_index)
                    .and_then(|p| p.line_segs.first())
                    .map(|seg| seg.vertical_pos),
// ==== replace ====
                PageItem::Table { para_index, .. } => paragraphs
                    .get(*para_index)
                    .and_then(|p| p.line_segs.first())
                    // [claude-hwpx tac-top-sb] 쪽 머리 글자처럼 취급 표에 그린 위 간격도 뺀다(본문 문단과 같은 값)
                    .map(|seg| {
                        let tac = paragraphs.get(*para_index).is_some_and(|p| {
                            p.controls.iter().any(|c| matches!(c, Control::Table(t) if t.common.treat_as_char))
                        });
                        seg.vertical_pos - if tac { claude_top_sb_hu(*para_index, seg) } else { 0 }
                    }),
