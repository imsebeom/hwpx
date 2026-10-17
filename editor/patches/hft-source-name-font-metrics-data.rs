// ==== find ====
fn claude_runtime_metric_decision<'a>(
// ==== replace ====
/// [claude-hwpx hft-source-name] 이 이름으로 실행 중에 등록한 폭 표가 있는가(대체 글꼴 대신 원래 이름으로 잴지 고를 때 묻는다).
pub(crate) fn claude_runtime_has_metric(name: &str) -> bool {
    if !CLAUDE_RUNTIME_ANY.load(std::sync::atomic::Ordering::Relaxed) {
        return false;
    }
    CLAUDE_RUNTIME_METRICS
        .get()
        .and_then(|lock| lock.read().ok())
        .is_some_and(|map| map.contains_key(name))
}

fn claude_runtime_metric_decision<'a>(
