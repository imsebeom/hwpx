// ==== find ====
    async execute(services) {
      await saveCurrentDocument(services);
    },
// ==== replace ====
    async execute(services) {
      // [claude-hwpx save-progress] 큰 문서는 저장에 시간이 걸린다. 메시지와 진행 막대를 띄우고 입력을 막는다(사용자 요청 2026-10-31).
      // 워커로 돌리지 않는다: 저장 중 입력을 받으면 끝날 때 「저장됨」 표시가 그 편집까지 지운다.
      // 막대는 transform 애니메이션이라 내보내기로 주 스레드가 멈춘 동안에도 움직인다.
      // 저장할 파일이 정해진 경우만(파일 고르기나 비밀번호 창을 가리면 안 된다)
      if (!services.wasm.currentFileHandle || services.wasm.requiresPasswordForSave) {
        await saveCurrentDocument(services);
        return;
      }
      const hold = document.createElement('div');
      hold.style.cssText = 'position:fixed;inset:0;z-index:2147483000;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,.18);cursor:wait';
      hold.innerHTML = '<style>@keyframes claude-save-bar{from{transform:translateX(-100%)}to{transform:translateX(250%)}}</style>'
        + '<div role="status" style="background:#fff;color:#222;border-radius:6px;padding:16px 22px;min-width:240px;box-shadow:0 4px 18px rgba(0,0,0,.25);font-size:13px">'
        + '<div style="margin-bottom:10px">저장하는 중입니다. 잠시 기다려 주세요.</div>'
        + '<div style="height:5px;background:#e3e6ea;border-radius:3px;overflow:hidden"><div style="height:100%;width:40%;background:#2f6fde;border-radius:3px;animation:claude-save-bar 1s linear infinite"></div></div>'
        + '</div>';
      hold.id = 'claude-save-progress';
      const block = (e: Event) => { e.stopPropagation(); e.preventDefault(); };
      window.addEventListener('keydown', block, true);
      window.addEventListener('keypress', block, true);
      document.body.append(hold);
      const shownAt = performance.now();
      try {
        await new Promise((r) => requestAnimationFrame(() => setTimeout(r, 30)));
        await saveCurrentDocument(services);
        const left = 350 - (performance.now() - shownAt);
        if (left > 0) await new Promise((r) => setTimeout(r, left));
      } finally {
        hold.remove();
        window.removeEventListener('keydown', block, true);
        window.removeEventListener('keypress', block, true);
      }
    },
