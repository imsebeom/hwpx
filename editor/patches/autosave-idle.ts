// ==== find ====
    idleDelayMs: settings.idleDelaySeconds * 1_000,
// ==== replace ====
    // [claude-hwpx autosave-idle] 복구본 내보내기는 49쪽 문서에서 주 스레드를 0.85초 막는다. 10초면 편집 중 잠깐 쉴 때마다 멈춰 60초를 하한으로 둔다
    idleDelayMs: Math.max(settings.idleDelaySeconds, 60) * 1_000,
