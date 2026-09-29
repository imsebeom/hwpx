// ==== find ====
    let (picture_control_index, picture) = host_pictures.next()?;
    if host_pictures.next().is_some() {
        return None;
    }
// ==== replace ====
    let (picture_control_index, picture) = host_pictures.next()?;
    if host_pictures.next().is_some() {
        return None;
    }
    // [claude-hwpx wrap-tab-empty-host] 글 없는 문단의 자리 차지 그림은 띠로 다루지 않는다. 한글은 그 빈 줄을 그림 뒤 윗자리에
    // 두고 다음 문단만 그림 아래로 보내는데(저장 사다리: 빈 줄 vpos = 문단 윗변, 다음 문단 = + 그림 상자 높이), 띠는 빈 줄까지
    // 그림 아래로 밀어 다음 문단이 한 줄 더 내려갔다. 렌더러의 빈 문단 자리 차지 규칙이 한글 저장본과 같은 결과를 낸다
    if picture.common.text_wrap == crate::model::shape::TextWrap::TopAndBottom
        && !host
            .text
            .chars()
            .any(|ch| ch > '\u{001F}' && ch != '\u{FFFC}' && !ch.is_whitespace())
    {
        return None;
    }
