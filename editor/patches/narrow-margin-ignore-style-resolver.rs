// ==== find ====
/// DocInfo 참조 테이블을 해소된 스타일 목록으로 변환한다.
// ==== replace ====
/// [claude-hwpx narrow-margin-ignore] 줄 폭(여백 적용 전, px)에서 왼쪽, 오른쪽 여백과 들여쓰기(양쪽 모두)를 뺀 가장 좁은 줄이 줄 폭의 25% 미만이면 한/글은
/// 그 문단의 여백과 들여쓰기를 모두 무시한다(d322 사본 실험: 줄 폭 5824 에서 남는 폭 1474 지킴, 1424 무시, 경계 1456).
pub(crate) fn claude_margins_ignored(style: &ResolvedParaStyle, full_px: f64) -> bool {
    let used = style.margin_left.max(0.0) + style.margin_right.max(0.0) + style.indent.abs();
    used > 0.0 && full_px > 0.0 && full_px - used < full_px * 0.25
}

/// DocInfo 참조 테이블을 해소된 스타일 목록으로 변환한다.
