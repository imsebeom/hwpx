// ==== find ====
  {
    id: 'view:zoom-fit-width',
    label: '폭 맞춤',
    shortcutLabel: 'Ctrl+G,W',
    execute(services) {
      applyZoomFit(services, 'fitWidth');
    },
  },
// ==== replace ====
  {
    id: 'view:zoom-fit-width',
    label: '폭 맞춤',
    shortcutLabel: 'Ctrl+G,W',
    execute(services) {
      applyZoomFit(services, 'fitWidth');
    },
  },
  // [claude-hwpx page-view-cmd] 상태 표시줄 한 쪽, 두 쪽 보기(사용자 요청 2026-10-03, 세 쪽 네 쪽은 10-25 뺌): 그 수만큼 쪽을 가로로 늘어놓고
  // 한 줄이 창에 다 들도록 쪽 맞춤한다. 확대/축소 대화상자의 「쪽 배치」와 같은 저장, 같은 이벤트를 쓴다
  ...[1, 2].map((n): CommandDef => ({
    id: `view:pages-${n}`,
    label: `${['한', '두'][n - 1]} 쪽 보기`,
    canExecute: (ctx) => ctx.hasDocument,
    execute(services) {
      if (!services.getViewportManager()) return;
      const arrangement: PageArrangement = n === 1
        ? { kind: 'single' }
        : { kind: 'multiple', columns: n, rows: 1 };
      const metrics = getZoomFitMetrics(services, arrangement);
      if (!metrics) return;
      const zoom = resolveZoomFitZoom('fitPage', metrics);
      if (zoom === null) return;
      userSettings.setPageViewSettings(arrangement, userSettings.getViewSettings().pageMovement, 'fitPage');
      const view = userSettings.getViewSettings();
      const transaction: PageViewSettingsChange = {
        arrangement: view.pageArrangement,
        pageMovement: view.pageMovement,
        zoom: { value: zoom, fitMode: view.zoomFitMode, anchor: CENTER_ZOOM_ANCHOR },
      };
      services.eventBus.emit('page-view-settings-changed', transaction);
      services.eventBus.emit('command-state-changed');
    },
  })),
  // 자동(10-25 사용자 요청): 대화상자의 「자동」과 같다. 배율은 그대로 두고, 낮은 배율에서 창에 드는 만큼 늘어놓는다
  {
    id: 'view:pages-auto',
    label: '자동 쪽 보기',
    canExecute: (ctx) => ctx.hasDocument,
    execute(services) {
      if (!services.getViewportManager()) return;
      userSettings.setPageViewSettings({ kind: 'auto' }, userSettings.getViewSettings().pageMovement, 'none');
      const view = userSettings.getViewSettings();
      const transaction: PageViewSettingsChange = {
        arrangement: view.pageArrangement,
        pageMovement: view.pageMovement,
        zoom: null,
      };
      services.eventBus.emit('page-view-settings-changed', transaction);
      services.eventBus.emit('command-state-changed');
    },
  },
