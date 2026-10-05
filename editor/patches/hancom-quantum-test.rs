// ==== find ====
    // condense=20 allows each measured space to shrink by 20%, saving 2px.
    reflow_line_segs(
        &mut para,
        ParagraphBox::content_width_px(48.0, 96.0),
// ==== replace ====
    // condense=20 allows each measured space to shrink by 20%, saving 2px.
    // [claude-hwpx hancom-quantum] 10px 글꼴은 글자 폭이 4 HWPUNIT 단위로 올라가 48.0px 에 4 HWPUNIT 모자란다.
    // 허용치 15 를 전제로 폭을 상자와 똑같이 맞춘 합성 시험이라 상자를 0.1px 넓힌다(줄임 동작 검증은 그대로).
    reflow_line_segs(
        &mut para,
        ParagraphBox::content_width_px(48.1, 96.0),
