// ==== find ====
    fn append_synthetic_cell_line(para: &mut Paragraph, capacity_hint: Option<u32>) -> bool {
// ==== replace ====
    fn append_synthetic_cell_line(para: &mut Paragraph, capacity_hint: Option<u32>) -> bool {
        // [claude-hwpx no-synth-cell-line] 한/글 2024 정답본과 맞대면 덧붙인 줄이 한/글 줄과 맞지 않는다(test/conformance/lab README).
        // 칸 높이는 줄 배치를 다시 짠 결과로 맞춘다. 아래 본문은 줄이 하나일 때만 덧붙이므로 여기서 돌려보내면 꺼진다.
        let _ = capacity_hint;
        if para.line_segs.len() == 1 {
            return false;
        }
