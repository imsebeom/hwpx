// ==== find ====
        assert!(
            (transient_bounds_h - 945.9).abs() <= 0.2,
            "{label}: transient bounds h={transient_bounds_h}"
        );
        assert!(
            (flushed_bounds_h - 945.9).abs() <= 0.2,
            "{label}: flushed bounds h={flushed_bounds_h}"
        );
// ==== replace ====
        // [claude-hwpx cut-row-pad-stored] HWPX 는 선언 높이가 여백뿐인 거대 칸도 원래 여백(141 + 141)을 쓴다(한/글 PDF 머리 행 간격 1486 HU)
        let expected_bounds_h = if label == "hwpx" { 947.8 } else { 945.9 };
        assert!(
            (transient_bounds_h - expected_bounds_h).abs() <= 0.2,
            "{label}: transient bounds h={transient_bounds_h}"
        );
        assert!(
            (flushed_bounds_h - expected_bounds_h).abs() <= 0.2,
            "{label}: flushed bounds h={flushed_bounds_h}"
        );
// ==== next ====
        let click_y = 1057.3;
// ==== replace ====
        // [claude-hwpx cut-row-pad-stored] HWPX 첫 조각은 아래 여백 141(1.9px)만큼 길어 재현점도 그만큼 내려간다(1061.0 -> 1062.9)
        let click_y = if path.ends_with(".hwpx") { 1059.2 } else { 1057.3 };
