// ==== find ====
/// 텍스트 폭 추정 (round 없이 raw px 반환)
// ==== replace ====
/// [claude-hwpx hancom-quantum] 한/글이 줄을 나눌 때 쓰는 글자 폭(1/1800 인치 = HWPUNIT/4 단위).
///
/// 한/글 2024 폭 사다리 실측(2026-10-05, 함초롬바탕 9~13pt, 굴림, 돋움, 바탕, 장평 50~120%, 자간 -10~+5%, 190여 건 전부 일치):
/// - 글자: 장평 100% 면 반올림, 아니면 (글자 폭 x 장평)을 버림
/// - 띄어쓰기(글자 크기의 절반짜리): 절반을 버림, 장평이 있으면 그 값에 곱해 반올림
/// - 자간: 그 글자 폭의 % 를 반올림
/// - 줄에 들어가는지는 이 값들의 합을 허용치 없이 본다
/// 종전에는 실수 폭을 더한 뒤 15 HWPUNIT 여유를 두어, 한/글이 꺾는 칸 글(9pt 「평가 시기」, 자리 3932 에 폭 3936)을 한 줄에 담았다.
///
/// 반환: (글자 폭, 자간). 점선 채움, 눌린 음수 자간, 조판이 덧붙인 간격이 있는 글자는 None(종전 실수 폭을 쓴다).
fn claude_hancom_advance_units(ch: char, style: &TextStyle) -> Option<(i64, i64)> {
    if style.extra_char_spacing != 0.0
        || style.extra_word_spacing != 0.0
        || matches!(ch, '\t' | '\n' | '\r')
    {
        return None;
    }
    let chars = [ch];
    let cluster_len = build_cluster_len(&chars);
    let decision = char_width_decision(&chars, &cluster_len, 0, style);
    let (font_size, ratio, _) = style_params(style);
    if decision.dash_leader
        || decision.negative_spacing_clamped
        || decision.base_width_px <= 0.0
        || font_size <= 0.0
        || ratio <= 0.0
    {
        return None;
    }
    const UNIT: f64 = 75.0 / 4.0;
    const EPS: f64 = 1e-6;
    let plain = (ratio - 1.0).abs() < 1e-9;
    let glyph = if ch == ' ' && (decision.base_width_px - font_size * 0.5).abs() < 1e-9 {
        let half = (font_size * UNIT / 2.0 + EPS).floor();
        if plain {
            half
        } else {
            (half * ratio + 0.5 + EPS).floor()
        }
    } else if plain {
        (decision.base_width_px * UNIT + 0.5 + EPS).floor()
    } else {
        (decision.base_width_px * ratio * UNIT + EPS).floor()
    };
    let spacing = if style.letter_spacing == 0.0 {
        0.0
    } else {
        (glyph * style.letter_spacing / font_size).round()
    };
    Some((glyph as i64, spacing as i64))
}

/// 줄 나눔용 전진 폭(px). 4 HWPUNIT 의 배수라 HWPUNIT 로 되돌리면 정수가 된다.
pub(crate) fn claude_hancom_advance_px(ch: char, style: &TextStyle) -> Option<f64> {
    claude_hancom_advance_units(ch, style)
        .map(|(glyph, spacing)| (glyph + spacing).max(0) as f64 * 4.0 / 75.0)
}

/// 위 전진 폭에 든 자간 몫(px). 줄 끝 글자의 자간을 뺄 때 쓴다.
pub(crate) fn claude_hancom_spacing_px(ch: char, style: &TextStyle) -> Option<f64> {
    claude_hancom_advance_units(ch, style).map(|(_, spacing)| spacing as f64 * 4.0 / 75.0)
}

/// 텍스트 폭 추정 (round 없이 raw px 반환)
