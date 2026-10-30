// ==== find ====
/// [claude-hwpx line-head-flags] 열 때: 글머리 비트가 규칙과 어긋난 문단만 고친다.
// ==== replace ====
/// [claude-hwpx stale-vpos-gap] 열 때: 떠 있는 개체가 없는 이웃 문단 사이가 앞 문단 끝보다 벌어져 있으면 낡은 값으로 보고 뒤 문단들을 당긴다.
/// 쪽이나 단이 바뀌어 위치가 되돌아가는 문단에서 당기기를 멈춘다. 한/글은 저장 세로 위치를 쓰지 않고 다시 쌓는다.
pub(crate) fn claude_close_stale_vpos_gaps(paras: &mut [Paragraph], shapes: &[crate::model::style::ParaShape]) {
    fn floats(p: &Paragraph) -> bool {
        p.controls.iter().any(|c| match c {
            Control::Table(t) => !t.common.treat_as_char,
            Control::Picture(x) => !x.common.treat_as_char,
            Control::Shape(s) => !s.common().treat_as_char,
            _ => false,
        })
    }
    let spacing = |p: &Paragraph| {
        shapes
            .get(p.para_shape_id as usize)
            .map(|s| (s.spacing_before, s.spacing_after))
            .unwrap_or((0, 0))
    };
    let mut shift = 0i32;
    let mut prev: Option<(i32, i32, bool)> = None; // 저장 끝 위치, 아래 간격, 떠 있는 개체
    for para in paras.iter_mut() {
        let is_float = floats(para);
        let Some(first) = para.line_segs.first() else {
            prev = None;
            shift = 0;
            continue;
        };
        let raw = first.vertical_pos;
        let new_area = raw == 0 || first.tag & (LineSeg::TAG_FIRST_LINE_OF_PAGE | LineSeg::TAG_FIRST_LINE_OF_COLUMN) != 0;
        let (before, after) = spacing(para);
        if new_area {
            shift = 0;
        } else if let Some((end, prev_after, prev_float)) = prev {
            let gap = raw - (end + prev_after + before);
            if gap < -2 {
                shift = 0;
            } else if gap > 2 && !is_float && !prev_float {
                shift += gap;
            }
        }
        let last = para.line_segs.last().unwrap();
        prev = Some((last.vertical_pos + last.line_height + last.line_spacing, after, is_float));
        if shift != 0 {
            for seg in para.line_segs.iter_mut() {
                seg.vertical_pos -= shift;
            }
        }
    }
    for para in paras.iter_mut() {
        for ctrl in para.controls.iter_mut() {
            if let Control::Table(t) = ctrl {
                for cell in t.cells.iter_mut() {
                    claude_close_stale_vpos_gaps(&mut cell.paragraphs, shapes);
                }
            }
        }
    }
}

/// [claude-hwpx line-head-flags] 열 때: 글머리 비트가 규칙과 어긋난 문단만 고친다.
