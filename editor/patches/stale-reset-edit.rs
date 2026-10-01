// ==== find ====
        let is_reset = is_original_lineseg
            && !is_ignored(pi)
            && prev_stored_bound.is_some_and(|bound| current_start < bound);

        let delta = if is_reset {
// ==== replace ====
        let is_reset = is_original_lineseg
            && !is_ignored(pi)
            && prev_stored_bound.is_some_and(|bound| current_start < bound);
        // [claude-hwpx stale-reset-edit] 저장 리셋(쪽 맨 위 vpos=0)은 저장할 때의 내용으로 한글이 쪽을 끊은 자리다.
        // 편집으로 앞 흐름이 밀렸으면(앞 문단 delta 가 0 이 아니거나, 편집 문단의 끝이 저장 끝과 다르면) 그 경계는
        // 더 이상 맞지 않는다 — 한글은 열 때 처음부터 다시 조판한다. 그대로 두면 앞 내용이 줄어도 표나 문단이
        // 새 쪽으로 밀려 쪽 아래가 비고, 저장본에 0 이 다시 써져 낡은 표시가 판마다 이어졌다(2026-10-02 가이드북
        // 3절 표 3-1, 4쪽을 21%만 채우고 5쪽으로). 흐름에 이어 붙이고, 그 뒤 리셋도 delta 캐리로 차례로 풀린다
        let claude_stale_reset = is_reset
            && !para_modified
            && (prev_delta != 0
                || (prev_idx == Some(start_para)
                    && !is_ignored(start_para)
                    && start_stored_end.is_some_and(|end| end != next_vpos)));
        let is_reset = is_reset && !claude_stale_reset;

        let delta = if claude_stale_reset {
            let gap = prev_idx
                .map(|pp| boundary_gap(&paragraphs[pp], &paragraphs[pi]))
                .unwrap_or(0);
            next_vpos.saturating_add(gap) - current_start
        } else if is_reset {
