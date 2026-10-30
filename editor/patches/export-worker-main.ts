// ==== find ====
  exportBytes: () => wasm.exportHwp(),
// ==== replace ====
  // [claude-hwpx export-worker-main] 복구본은 워커에서 내보낸다(주 스레드에서는 49쪽 문서가 약 1초 멈춘다). 플러그인도 같은 경로를 쓴다
  // hwpx 문서의 복구본은 hwpx 로. hwp 로 저장하면 다시 열 때 다른 조판 규칙을 타고 메모를 잃는다(49쪽 → 51쪽, 2026-10-30)
  exportBytes: () => wasm.exportInWorker(wasm.getSourceFormat() === 'hwpx' ? 'hwpx' : 'hwp'),
// ==== next ====
autosaveManager.connect(eventBus);
// ==== replace ====
autosaveManager.connect(eventBus);
(window as unknown as { __claudeIsDirty?: unknown }).__claudeIsDirty = () => documentState.isDirty();
(window as unknown as { __claudeExportInWorker?: unknown }).__claudeExportInWorker = (kind: 'hwp' | 'hwpx', postTo?: string) => wasm.exportInWorker(kind, postTo);
// ==== next ====
  const fileName = recoveryFileName(draft.fileName);
// ==== replace ====
  const fileName = recoveryFileName(draft.fileName, new Uint8Array(draft.data));
