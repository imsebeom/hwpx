// ==== find ====
                    if t.caption.is_some()
                        || (p.line_segs[0].line_height - (t.common.height as i32 + outer)).abs() > 75
                    {
// ==== replace ====
                    // [claude-hwpx restate-short-line] 줄이 표 + 여백보다 짧으면 낡은 줄이다(한/글은 줄을 표보다 짧게 쓰지 않는다) — 다시 잰다(c70 10번: 줄 50775, 표 60135)
                    // 표의 절반도 안 되는 줄(생성기 더미 줄 배치 900)은 대상이 아니다(서식2 c52, c69 에서 나빠짐)
                    let claude_short_line = p.line_segs[0].line_height < t.common.height as i32 + outer - 75
                        && p.line_segs[0].line_height * 2 >= t.common.height as i32 + outer;
                    if t.caption.is_some()
                        || (!claude_short_line
                            && (p.line_segs[0].line_height - (t.common.height as i32 + outer)).abs() > 75)
                    {
// ==== next ====
                let p = &mut doc.document.sections[si].paragraphs[pi];
                let Some(Control::Table(t)) = p.controls.get_mut(ci) else {
                    continue;
                };
                let old_h = t.common.height as i32;
                if new_h <= 0 || (new_h - old_h).abs() < 75 {
// ==== replace ====
                let p = &mut doc.document.sections[si].paragraphs[pi];
                // [claude-hwpx restate-short-line] 짧은 줄은 표 높이가 그대로여도 고친다
                let claude_short_line = match p.controls.get(ci) {
                    Some(Control::Table(t)) => {
                        let full = t.common.height as i32 + t.outer_margin_top as i32 + t.outer_margin_bottom as i32;
                        p.line_segs[0].line_height < full - 75 && p.line_segs[0].line_height * 2 >= full
                    }
                    _ => false,
                };
                let Some(Control::Table(t)) = p.controls.get_mut(ci) else {
                    continue;
                };
                let old_h = t.common.height as i32;
                if new_h <= 0 || ((new_h - old_h).abs() < 75 && !claude_short_line) {
