// ==== find ====
        let last = para.line_segs.last().unwrap();
        prev = Some((last.vertical_pos + last.line_height + last.line_spacing, after, is_float));
// ==== replace ====
        // [claude-hwpx stale-line-height] 표 문단 글 줄의 저장 높이가 표 높이로 적혀 있어도(d007: 7176, 다음 줄과 1760 차이) 한/글은 줄 위치 차이만큼만 나아간다
        if para.controls.iter().any(|c| matches!(c, Control::Table(t) if t.common.treat_as_char)) {
            for i in 1..para.line_segs.len() {
                let (cur, next) = (para.line_segs[i - 1].clone(), para.line_segs[i].vertical_pos);
                let diff = next - cur.vertical_pos;
                if diff > 0 && cur.line_height + cur.line_spacing > diff + 2 {
                    para.line_segs[i - 1].line_height = (diff - cur.line_spacing).max(cur.text_height.min(diff));
                }
            }
        }
        let last = para.line_segs.last().unwrap();
        prev = Some((last.vertical_pos + last.line_height + last.line_spacing, after, is_float));
// ==== next ====
        if shift != 0 {
            for seg in para.line_segs.iter_mut() {
                seg.vertical_pos -= shift;
            }
        }
// ==== replace ====
        if shift != 0 {
            for seg in para.line_segs.iter_mut() {
                seg.vertical_pos -= shift;
            }
        }
        // [claude-hwpx stale-tac-line] 한 줄 문단의 글자처럼 취급 표보다 줄이 짧으면(표를 키우고 줄을 안 고친 낡은 값) 표 높이로 맞추고 뒤 문단을 민다. 절반 미만은 더미 줄이라 뺀다
        if para.line_segs.len() == 1 {
            let target = para.controls.iter().find_map(|c| match c {
                Control::Table(t) if t.common.treat_as_char => {
                    Some(t.common.height as i32 + t.outer_margin_top as i32 + t.outer_margin_bottom as i32)
                }
                _ => None,
            });
            if let Some(target) = target {
                let h = para.line_segs[0].line_height;
                if h < target - 2 && h * 2 >= target {
                    para.line_segs[0].line_height = target;
                    para.line_segs[0].text_height = para.line_segs[0].text_height.max(target);
                    shift -= target - h;
                }
            }
        }
