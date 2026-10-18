// ==== find ====
    if para.text.is_empty() {
        // [#4677] 각 인라인 개체의 **UTF-16 오프셋**을 함께 들고 다닌다. lineseg 의
// ==== replace ====
    // [claude-hwpx ws-multi-tac] 빈칸만 든 문단에 글자처럼 취급 표가 둘 이상이면 글 없는 문단처럼 개체 폭으로 줄을 나눈다
    // (d159 p0: 한/글은 줄 폭에 가까운 표 둘을 두 줄로 놓는데 엔진 줄 나눔은 표 폭을 세지 않아 한 줄에 겹쳤다)
    let claude_ws_tac = !para.text.is_empty()
        && para.text.chars().all(char::is_whitespace)
        && para
            .controls
            .iter()
            .filter(|c| matches!(c, Control::Table(t) if t.common.treat_as_char))
            .count()
            >= 2;
    if para.text.is_empty() || claude_ws_tac {
        // [#4677] 각 인라인 개체의 **UTF-16 오프셋**을 함께 들고 다닌다. lineseg 의
// ==== next ====
            .scan(0u32, |utf16_pos, ctrl| {
                let start = *utf16_pos;
                if ctrl.occupies_ctrl_char_slot() {
                    *utf16_pos += CTRL_CHAR_CODE_UNITS;
                }
                Some((start, ctrl))
            })
            .filter_map(|(start, ctrl)| inline_control_size_hwp(ctrl).map(|size| (start, size)))
// ==== replace ====
            .scan(0u32, |utf16_pos, ctrl| {
                let start = *utf16_pos;
                if ctrl.occupies_ctrl_char_slot() {
                    *utf16_pos += CTRL_CHAR_CODE_UNITS;
                }
                Some((start, ctrl))
            })
            // [claude-hwpx ws-multi-tac] 빈칸이 섞이면 개체 위치를 원래 스트림 위치로(빈칸 몫 포함)
            .zip(claude_ws_tac.then(|| para.control_utf16_positions()).unwrap_or_default().into_iter().map(Some).chain(std::iter::repeat(None)))
            .map(|((start, ctrl), raw)| (raw.unwrap_or(start), ctrl))
            .filter_map(|(start, ctrl)| inline_control_size_hwp(ctrl).map(|size| (start, size)))
