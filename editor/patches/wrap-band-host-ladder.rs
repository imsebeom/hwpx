// ==== find ====
    let synth = crate::model::paragraph::LineSeg::TAG_IMPLEMENTATION_PROPERTY;
    if cur.line_segs.iter().any(|s| s.tag & synth != 0) || next_seg.tag & synth != 0 {
        return None;
    }
// ==== replace ====
    let synth = crate::model::paragraph::LineSeg::TAG_IMPLEMENTATION_PROPERTY;
    // [claude-hwpx wrap-band-host-ladder] 그림 띠가 방금 새로 짠 빈 호스트(좌우 조각으로 나뉜 한 줄, 뒤 문단도 같은 띠)는
    // 낡은 사다리가 아니라 한글 저장 사다리와 같은 값이다. 여기서 물러나면 휴리스틱이 줄을 한 번 더 예약해, 어울림 그림을
    // 새 문단으로 옮겼을 때 옆 글이 한 줄 아래에서 시작했다(한글 저장본은 같은 값으로 한 줄 위)
    let fresh_band_host = cur.line_segs.len() >= 2
        && cur.line_segs.iter().all(|s| s.tag & synth != 0)
        && crate::renderer::height_measurer::stored_seg_is_row_fragment(cur, 1);
    if !fresh_band_host
        && (cur.line_segs.iter().any(|s| s.tag & synth != 0) || next_seg.tag & synth != 0)
    {
        return None;
    }
