// ==== find ====
        &source_line_segs[..0]
    } else if line_seg_axis_end > 0 {
// ==== replace ====
        &source_line_segs[..0]
    } else if line_seg_inside_slot(para, source_line_segs) {
        // [claude-hwpx seg-inside-slot] 줄 시작이 컨트롤 8칸 한가운데면 한/글이 그 문단부터 끝까지 버린다(Open False, 17쪽 → 3쪽).
        // 빼면 한/글이 열 때 다시 잰다
        &source_line_segs[..0]
    } else if line_seg_axis_end > 0 {
// ==== next ====
/// Paragraph 하나를 (완전한 `<hp:run>` 시퀀스 XML, `<hp:linesegarray>` 요소 XML,
// ==== replace ====
/// [claude-hwpx seg-inside-slot] 글 사이와 글 뒤의 컨트롤 칸(8칸 단위)을 구해 줄 시작이 그 안쪽을 가리키는지 본다.
fn line_seg_inside_slot(para: &Paragraph, segs: &[LineSeg]) -> bool {
    let chars: Vec<char> = para.text.chars().collect();
    if para.char_offsets.len() != chars.len() {
        return false;
    }
    let mut gaps = Vec::new();
    let mut prev_end = 0u32;
    for (i, &c) in chars.iter().enumerate() {
        let off = para.char_offsets[i];
        if off > prev_end {
            gaps.push((prev_end, off));
        }
        prev_end = off + char_utf16_width(c);
    }
    let end = para.char_count.saturating_sub(1);
    if end > prev_end {
        gaps.push((prev_end, end));
    }
    segs.iter().any(|s| {
        gaps.iter().any(|&(a, b)| {
            (b - a) % 8 == 0 && s.text_start > a && s.text_start < b && (s.text_start - a) % 8 != 0
        })
    })
}

/// Paragraph 하나를 (완전한 `<hp:run>` 시퀀스 XML, `<hp:linesegarray>` 요소 XML,
