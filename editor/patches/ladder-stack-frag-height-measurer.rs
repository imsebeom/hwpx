// ==== find ====
                    let (mut next_top, mut end) = (0i32, 0i32);
                    for s in c.paragraphs.iter().flat_map(|p| p.line_segs.iter()) {
                        let top = s.vertical_pos.max(next_top);
                        end = end.max(top.saturating_add(s.line_height));
                        next_top = top.saturating_add(s.line_height).saturating_add(s.line_spacing.max(0));
                    }
// ==== replace ====
                    let (mut next_top, mut end) = (0i32, 0i32);
                    // [claude-hwpx ladder-stack-frag] 같은 위치의 가로 조각 줄은 같은 줄, 줄 간격은 음수도 그대로(d020: 조각 2468 둘, 간격 -1040)
                    let mut claude_prev: Option<(i32, i32)> = None;
                    for s in c.paragraphs.iter().flat_map(|p| p.line_segs.iter()) {
                        let frag = claude_prev.filter(|&(v, _)| v == s.vertical_pos);
                        let top = frag.map(|(_, t)| t).unwrap_or_else(|| s.vertical_pos.max(next_top));
                        end = end.max(top.saturating_add(s.line_height));
                        let nt = top.saturating_add(s.line_height).saturating_add(s.line_spacing);
                        next_top = if frag.is_some() { next_top.max(nt) } else { nt };
                        claude_prev = Some((s.vertical_pos, top));
                    }
// ==== next ====
                    let (mut next_top, mut end) = (0i64, 0i64);
                    for s in cell.paragraphs.iter().flat_map(|p| p.line_segs.iter()) {
                        let top = i64::from(s.vertical_pos).max(next_top);
                        end = end.max(top + i64::from(s.line_height));
                        next_top = top + i64::from(s.line_height) + i64::from(s.line_spacing.max(0));
                    }
// ==== replace ====
                    let (mut next_top, mut end) = (0i64, 0i64);
                    // [claude-hwpx ladder-stack-frag] 같은 위치의 가로 조각 줄은 같은 줄, 줄 간격은 음수도 그대로
                    let mut claude_prev: Option<(i32, i64)> = None;
                    for s in cell.paragraphs.iter().flat_map(|p| p.line_segs.iter()) {
                        let frag = claude_prev.filter(|&(v, _)| v == s.vertical_pos);
                        let top = frag.map(|(_, t)| t).unwrap_or_else(|| i64::from(s.vertical_pos).max(next_top));
                        end = end.max(top + i64::from(s.line_height));
                        let nt = top + i64::from(s.line_height) + i64::from(s.line_spacing);
                        next_top = if frag.is_some() { next_top.max(nt) } else { nt };
                        claude_prev = Some((s.vertical_pos, top));
                    }
// ==== next ====
                    let (mut next_top, mut end) = (0i64, 0i64);
                    for seg in cell.paragraphs.iter().flat_map(|p| p.line_segs.iter()) {
                        let top = i64::from(seg.vertical_pos).max(next_top);
                        end = end.max(top + i64::from(seg.line_height));
                        next_top = top + i64::from(seg.line_height) + i64::from(seg.line_spacing.max(0));
                    }
// ==== replace ====
                    let (mut next_top, mut end) = (0i64, 0i64);
                    // [claude-hwpx ladder-stack-frag] 같은 위치의 가로 조각 줄은 같은 줄, 줄 간격은 음수도 그대로
                    let mut claude_prev: Option<(i32, i64)> = None;
                    for seg in cell.paragraphs.iter().flat_map(|p| p.line_segs.iter()) {
                        let frag = claude_prev.filter(|&(v, _)| v == seg.vertical_pos);
                        let top = frag.map(|(_, t)| t).unwrap_or_else(|| i64::from(seg.vertical_pos).max(next_top));
                        end = end.max(top + i64::from(seg.line_height));
                        let nt = top + i64::from(seg.line_height) + i64::from(seg.line_spacing);
                        next_top = if frag.is_some() { next_top.max(nt) } else { nt };
                        claude_prev = Some((seg.vertical_pos, top));
                    }
