// ==== find ====
        let click_y = if path.ends_with(".hwpx") { 1059.2 } else { 1057.3 };
// ==== replace ====
        // [claude-hwpx test-1949-omtop] partial-omtop-hwpx 로 HWPX 첫 조각이 바깥 위 여백 283(3.8px)만큼 더 내려간다(하단 1066.7, 한/글 PDF 와 0.4pt 안)
        let click_y = if path.ends_with(".hwpx") { 1063.0 } else { 1057.3 };
