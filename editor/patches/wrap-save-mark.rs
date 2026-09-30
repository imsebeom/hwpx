// ==== find ====
        // This staging core owns the section source and every changed LineSeg
        // together. The caller can expose it only after convergence succeeds.
// ==== replace ====
        // [claude-hwpx wrap-save-mark] 편집이 새로 짠 줄(띠 줄, 띠에서 풀린 문단의 줄)에 표시 비트(1 << 30, 파일에는 쓰지 않는다)를
        // 붙여 저장기가 파일에 남기게 한다(wrap-save-band). 합성 줄로 빠지면 다시 열 때 rhwp 가 세로 위치를 새로 매기다
        // 좌우 조각을 한 줄씩 쌓거나 옛 자리로 돌려 글이 그림과 겹쳤다(2026-09-30 저장 왕복 대조 7건)
        for paragraph in &mut staged_paragraphs[recalc_from.min(new_range.start)..affected_end] {
            for seg in &mut paragraph.line_segs {
                seg.tag |= 1 << 30;
            }
        }
        // This staging core owns the section source and every changed LineSeg
        // together. The caller can expose it only after convergence succeeds.
