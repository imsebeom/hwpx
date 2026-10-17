// ==== find ====
    let Some(slots) = metric_index().get(alias_resolved_name) else {
        return claude_runtime_metric_decision(name, alias_resolved_name, alias_rule_id, bold);
    };
// ==== replace ====
    // [claude-hwpx font-file-first] 실행 중에 등록한 표(설치된 글꼴 파일)가 있으면 내장 표보다 먼저 쓴다. 한/글 2024 는 글꼴 파일의
    // 전진 폭으로 조판한다(test/conformance/lab e2, e5). 무엇을 등록할지는 에디터 font-metrics.mjs 가 정한다.
    if let Some(decision) = claude_runtime_metric_decision(name, alias_resolved_name, alias_rule_id, bold) {
        return Some(decision);
    }
    let Some(slots) = metric_index().get(alias_resolved_name) else {
        return None;
    };
// ==== next ====
        if name.is_empty() || em == 0 || em > u64::from(u16::MAX) || claude_has_builtin_metric(name)
        {
// ==== replace ====
        // 내장 표가 있는 글꼴도 받는다(위 font-file-first). 무엇을 보낼지는 에디터가 정한다
        if name.is_empty() || em == 0 || em > u64::from(u16::MAX) {
