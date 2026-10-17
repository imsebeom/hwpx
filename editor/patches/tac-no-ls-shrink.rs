// ==== find ====
        let table_height = if table.common.treat_as_char
            && common_h > 0.0
            && raw_table_height > common_h + shrink_threshold
// ==== replace ====
        // [claude-hwpx tac-no-ls-shrink] rhwp#7419 — 생성기가 쓴 표(저장 LINE_SEG 가 하나도 없다)는 한글이 열 때
        // 줄 배치와 표 높이를 다시 계산하므로 선언높이가 내용을 누르지 않는다. 내용이 그보다 크면 한글은 행을 키운다
        // (재현: 셀 2400+2400, 표 4800 → 한글 재저장 5284, 행 32.0+38.5px). 여기서 줄이면 두 줄이 한 줄 칸에 눌려
        // 아래 표와 겹친다. 처음에는 「선언높이 = 행별 셀 선언높이 합」인 표로 한정했으나, 선언높이가 칸 합과 다른
        // 생성기 표도 한글은 키운다(2026-10-17 KTX 문항 자료 1: 칸 합 23107, 표 28680, 내용 1.25배 → 한글 재저장 36121,
        // 안쪽 표 1560 → 9000). 줄여 그리면 바깥 칸이 눌려 안쪽 표 행이 잘렸다.
        let generator_restated_height = !self.is_native_hwp5
            && table.cells.iter().all(|c| {
                c.paragraphs.iter().all(crate::renderer::para_has_no_stored_line_segs)
            });
        let table_height = if table.common.treat_as_char
            && !generator_restated_height
            && common_h > 0.0
            && raw_table_height > common_h + shrink_threshold