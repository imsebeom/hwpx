// ==== find ====
  exportBytes: () => wasm.exportHwp(),
// ==== replace ====
  // [claude-hwpx export-worker-main] 복구본은 워커에서 내보낸다(주 스레드에서는 49쪽 문서가 약 1초 멈춘다). 플러그인도 같은 경로를 쓴다
  exportBytes: () => wasm.exportInWorker('hwp'),
// ==== next ====
autosaveManager.connect(eventBus);
// ==== replace ====
autosaveManager.connect(eventBus);
(window as unknown as { __claudeExportInWorker?: unknown }).__claudeExportInWorker = (kind: 'hwp' | 'hwpx', postTo?: string) => wasm.exportInWorker(kind, postTo);
