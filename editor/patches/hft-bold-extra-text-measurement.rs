// ==== find ====
    // [claude-hwpx dash-natural] 한/글은 하이픈 묶음도 글꼴 폭으로 둔다(사본 실험 6종).
// ==== replace ====
    // [claude-hwpx hft-bold-extra] 한컴 내장 글꼴(한양, 신명 계열, 명조)의 굵은 글자는 0.05em 넓다(빈칸 제외, 장평과 자간은 그 위에 곱함 — lab 실험 bh, bh2)
    let base_width_raw = base_width_raw + claude_hft_bold_extra_px(style, c, font_size);
    // [claude-hwpx dash-natural] 한/글은 하이픈 묶음도 글꼴 폭으로 둔다(사본 실험 6종).
// ==== next ====
            .map(|width| f64::from(width) * font_size / f64::from(lookup.metric.em_size)),
        _ => None,
    }
    .unwrap_or(decision.base_width_px);
// ==== replace ====
            .map(|width| f64::from(width) * font_size / f64::from(lookup.metric.em_size))
            // [claude-hwpx hft-bold-extra] 표를 다시 읽으므로 굵게 늘림도 다시 더한다(어림값 쪽은 decision 에 이미 들어 있다)
            .map(|px| px + claude_hft_bold_extra_px(style, ch, font_size)),
        _ => None,
    }
    .unwrap_or(decision.base_width_px);
// ==== next ====
/// [claude-hwpx hancom-quantum] 한/글이 줄을 나눌 때 쓰는 글자 폭(1/1800 인치 = HWPUNIT/4 단위).
// ==== replace ====
/// [claude-hwpx hft-bold-extra] 한컴 내장 글꼴(PDF 에 T1 로 박히는 한양, 신명 계열, 명조)의 굵은 글자는 글자마다 0.05em 넓다(빈칸 제외).
/// 설치된 TTF 로 그리는 글꼴(휴먼명조 등)과 다른 글꼴로 바뀌는 글꼴은 늘지 않는다(lab 실험 bh, bh2).
fn claude_hft_bold_extra_px(style: &TextStyle, c: char, font_size: f64) -> f64 {
    if style.bold
        && !c.is_whitespace()
        && (style.font_family.starts_with("한양")
            || style.font_family.starts_with("신명")
            || style.font_family == "명조")
    {
        font_size * 0.05
    } else {
        0.0
    }
}

/// [claude-hwpx hancom-quantum] 한/글이 줄을 나눌 때 쓰는 글자 폭(1/1800 인치 = HWPUNIT/4 단위).
