// ==== find ====
    let all_synthetic = !axis_line_segs.is_empty()
        && axis_line_segs
            .iter()
            .all(|s| s.tag & LineSeg::TAG_IMPLEMENTATION_PROPERTY != 0);
// ==== replace ====
    // [claude-hwpx wrap-save-band] 에디터 편집이 새로 짠 줄(표시 비트 1 << 30, wrap-save-mark — 그림 띠 줄과 띠에서 풀린
    // 문단의 줄)은 합성 줄이어도 파일에 남긴다. 빠지면 다시 열 때 rhwp 가 세로 위치를 새로 매기며 좌우 조각을 한 줄씩
    // 쌓거나 문단을 폭 전체로 다시 나눠 글이 그림과 겹쳤다(2026-09-30 저장 왕복 대조 101건 중 7건). 표시가 없는 합성 줄
    // (줄 배치 없이 열어 rhwp 가 만든 줄)은 종전대로 뺀다(#5847). 한글은 남긴 줄로도 같은 결과를 낸다(10건 PDF 대조)
    let edit_rows = axis_line_segs.iter().any(|s| s.tag & (1 << 30) != 0);
    let all_synthetic = !edit_rows
        && !axis_line_segs.is_empty()
        && axis_line_segs
            .iter()
            .all(|s| s.tag & LineSeg::TAG_IMPLEMENTATION_PROPERTY != 0);
    // 남기는 줄은 두 비트를 떼어 쓴다 — 구현 비트가 남으면 다시 열 때 파서가 합성 줄로 보고 세로 위치를 줄마다 새로
    // 매겼다. 한글이 저장하는 줄과 같은 모양(비트 없음)이 된다
    let edit_cleared: Vec<LineSeg>;
    let axis_line_segs: &[LineSeg] = if edit_rows {
        edit_cleared = axis_line_segs
            .iter()
            .map(|seg| {
                let mut seg = seg.clone();
                seg.tag &= !(LineSeg::TAG_IMPLEMENTATION_PROPERTY | (1 << 30));
                seg
            })
            .collect();
        &edit_cleared
    } else {
        axis_line_segs
    };
