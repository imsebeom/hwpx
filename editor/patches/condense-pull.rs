// ==== find ====
fn text_token_fits_line_hwp(
    current_width_hwp: i32,
// ==== replace ====
// [claude-hwpx condense-pull] 최소 공백(공백을 줄여 글을 당겨 담기)을 한/글처럼 쓴다.
//
// 한/글 재저장 317개 문서 대조(2026-10-06): 공백을 줄여야 들어가는 토큰은
// - 낱말을 잇는 글자(앞이 공백이 아님)면 줄인 폭으로 들어가는 한 담고,
// - 새 낱말의 첫 토큰이면 「그 앞 띄어쓰기를 뺀 줄 내용」이 아직 자연 폭 안일 때만 담는다.
//   이미 공백을 줄여 채운 줄에는 새 낱말을 더 당겨 오지 않는다.
// 종전 규칙(줄에 글자 2.5개분 넘게 남았을 때만 당김)은 줄 끝에서 쪼개진 낱말을 마저 담지 못해
// 최소 공백을 쓴 문서(나눔스퀘어 지도안 등)에서 한/글보다 두세 글자씩 덜 담았다(문단 215개 고침, 11개 나빠짐).
thread_local! {
    static CLAUDE_TOKEN_CONTINUES_WORD: std::cell::Cell<bool> = const { std::cell::Cell::new(false) };
    static CLAUDE_TRAILING_SPACE_HWP: std::cell::Cell<i32> = const { std::cell::Cell::new(0) };
    static CLAUDE_TOKEN_LEADING_SPACE_HWP: std::cell::Cell<i32> = const { std::cell::Cell::new(0) };
}

/// 글 토큰을 줄에 넣어 보기 전에 부른다: 낱말을 잇는지, 바로 앞 띄어쓰기 폭이 얼마인지 적어 둔다.
fn claude_note_token_start(text_chars: &[char], start_idx: usize) {
    let continues = start_idx > 0
        && text_chars
            .get(start_idx - 1)
            .is_some_and(|prev| !prev.is_whitespace());
    CLAUDE_TOKEN_CONTINUES_WORD.with(|flag| flag.set(continues));
    let lead = CLAUDE_TRAILING_SPACE_HWP.with(|width| width.replace(0));
    CLAUDE_TOKEN_LEADING_SPACE_HWP.with(|width| width.set(if continues { 0 } else { lead }));
}

fn text_token_fits_line_hwp(
    current_width_hwp: i32,
// ==== next ====
    let condense_pull_allowed = !needs_condense_to_fit
        || condense_fit_can_pull_next_token(
            current_width_hwp,
            space_savings_hwp,
            effective_width_hwp,
            max_font_size,
        );
// ==== replace ====
    let _ = max_font_size;
    let condense_pull_allowed = !needs_condense_to_fit
        || CLAUDE_TOKEN_CONTINUES_WORD.with(|flag| flag.get())
        || current_width_hwp - CLAUDE_TOKEN_LEADING_SPACE_HWP.with(|width| width.get())
            <= effective_width_hwp;
// ==== next ====
fn condense_fit_can_pull_next_token(
// ==== replace ====
#[allow(dead_code)]
fn condense_fit_can_pull_next_token(
// ==== next ====
            BreakToken::Text {
                start_idx,
                end_idx,
                base_width,
                max_font_size,
                base_char_widths,
                ..
            } => {
// ==== replace ====
            BreakToken::Text {
                start_idx,
                end_idx,
                base_width,
                max_font_size,
                base_char_widths,
                ..
            } => {
                claude_note_token_start(text_chars, *start_idx);
// ==== next ====
            BreakToken::Text {
                start_idx,
                end_idx,
                width,
                max_font_size,
                ref char_widths,
                ..
            } => {
// ==== replace ====
            BreakToken::Text {
                start_idx,
                end_idx,
                width,
                max_font_size,
                ref char_widths,
                ..
            } => {
                claude_note_token_start(text_chars, *start_idx);
// ==== next ====
                let space_hwp = to_hwp(*width);
                cursor.lw += space_hwp;
// ==== replace ====
                let space_hwp = to_hwp(*width);
                cursor.lw += space_hwp;
                CLAUDE_TRAILING_SPACE_HWP.with(|width| width.set(width.get() + space_hwp));
// ==== next ====
                let space_hwp = to_hwp(*width);
                lw += space_hwp;
// ==== replace ====
                let space_hwp = to_hwp(*width);
                lw += space_hwp;
                CLAUDE_TRAILING_SPACE_HWP.with(|width| width.set(width.get() + space_hwp));
