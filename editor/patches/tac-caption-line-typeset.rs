// ==== find ====
        let height_for_fit = if has_tac {
            first_line_tac_height.unwrap_or(fmt.height_for_fit)
        } else {
// ==== replace ====
        // [claude-hwpx tac-caption-line] 한 줄짜리 표 문단은 쪽 끝에서 문단 아래 간격 없이 「위 간격 + 줄 높이」만 들어가면
        // 된다(한/글 e13 의 마지막 줄 규칙). 캡션을 넣어 줄 높이가 한/글과 같아지자 d221 의 쪽 높이 표(67846)가 아래
        // 간격 6.7px 때문에 다음 쪽으로 밀렸다
        let height_for_fit = if has_tac {
            first_line_tac_height.unwrap_or(if fmt.line_heights.len() == 1 {
                fmt.spacing_before + fmt.line_heights[0]
            } else {
                fmt.height_for_fit
            })
        } else {
