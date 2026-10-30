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
