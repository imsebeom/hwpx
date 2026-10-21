// ==== find ====
async function runPdfPrint(services: CommandServices): Promise<void> {
// ==== replace ====
// [claude-hwpx print-fallback] guidance=false: 안내 창 없이 바로 준비해 브라우저 인쇄 창을 연다(인쇄 미리보기 창을 못 쓸 때)
async function runPdfPrint(services: CommandServices, guidance = true): Promise<void> {
// ==== next ====
    const showGuidance = userSettings.getShowPdfPrintGuidance();
// ==== replace ====
    const showGuidance = guidance && userSettings.getShowPdfPrintGuidance();
// ==== next ====
  let surface: PrintPreviewSurface | null = null;
  let keepPreviewOpen = false;
  let restoreStatus = true;
// ==== replace ====
  let surface: PrintPreviewSurface | null = null;
  let keepPreviewOpen = false;
  let restoreStatus = true;
  let fallback = false;
// ==== next ====
    surface = await surfacePromise;
    if (!surface) return;
// ==== replace ====
    surface = await surfacePromise;
    if (!surface) { fallback = true; return; }
// ==== next ====
    if (err instanceof PrintPreviewBlockedError) {
      alert('인쇄 미리보기 팝업이 차단되었습니다. 팝업 허용 후 다시 시도해주세요.');
    } else {
      showToast({ message: `인쇄 미리보기에 실패했습니다: ${msg}`, durationMs: 5000 });
    }
  } finally {
    if (!keepPreviewOpen) surface?.close();
    printJobActive = false;
    if (restoreStatus && statusEl) statusEl.textContent = originalStatus;
  }
}
// ==== replace ====
    // 미리보기 새 창이 막히거나(팝업 차단) 열려도 못 쓰면(앱 창, 시간 초과) 멈추거나 경고로 끝내지 않고
    // 화면 안 숨은 틀에서 바로 브라우저 인쇄 창을 연다(2026-10-21 로컬 에디터 「팝업 차단」, 「준비하고 있습니다」에서 멈춤)
    fallback = true;
    console.warn('[file:print] 미리보기 창 대신 화면 안 인쇄로 넘어간다:', msg, err instanceof PrintPreviewBlockedError ? '(팝업 차단)' : '');
  } finally {
    if (!keepPreviewOpen) surface?.close();
    printJobActive = false;
    if (restoreStatus && statusEl) statusEl.textContent = originalStatus;
  }
  if (fallback) await runPdfPrint(services, false);
}
