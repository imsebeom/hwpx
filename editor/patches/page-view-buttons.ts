// ==== find ====
  // 폭 맞춤·쪽 맞춤은 메뉴/단축키와 같은 커맨드를 탄다 — 계산과 저장 자리가 하나여야 한다.
// ==== replace ====
  // [claude-hwpx page-view-buttons] 한 쪽, 두 쪽, 자동 보기 단추를 폭 맞춤 앞에 둔다(명령은 page-view-cmd).
  // 그림은 쪽 수만큼 세운 네모(자동은 「자동」 글자)이고, 지금 배치에 맞는 단추를 눌린 모양으로 보인다
  {
    const fitWidth = document.getElementById('sb-zoom-fit-width')!;
    const group = document.createElement('span');
    group.className = 'stb-page-view-group';
    const buttons: HTMLButtonElement[] = [];
    for (const n of [1, 2, 0]) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'stb-icon-btn stb-page-view-btn';
      btn.title = n === 0 ? '자동 쪽 보기' : `${['한', '두'][n - 1]} 쪽 보기`;
      btn.setAttribute('aria-label', btn.title);
      if (n === 0) {
        btn.classList.add('stb-page-view-auto');
        btn.textContent = '자동';
      } else {
        const w = n * 7 + (n - 1) * 2;
        const rects = Array.from({ length: n }, (_, i) => `<rect x="${i * 9 + 0.5}" y="0.5" width="6" height="9" rx="0.5"></rect>`).join('');
        btn.innerHTML = `<svg class="stb-page-view-icon" width="${w}" height="10" viewBox="0 0 ${w} 10" aria-hidden="true" focusable="false">${rects}</svg>`;
      }
      btn.addEventListener('click', () => {
        dispatcher.dispatch(`view:pages-${n === 0 ? 'auto' : n}`);
      });
      btn.dataset.pages = String(n);
      buttons.push(btn);
      group.appendChild(btn);
    }
    fitWidth.before(group);
    const syncPageViewButtons = () => {
      const a = userSettings.getViewSettings().pageArrangement;
      const n = a.kind === 'auto' ? 0 : a.kind === 'single' ? 1 : a.kind === 'double' ? 2 : a.kind === 'multiple' && a.rows === 1 ? a.columns : -1;
      buttons.forEach((btn) => {
        const on = btn.dataset.pages === String(n);
        btn.classList.toggle('active', on);
        btn.setAttribute('aria-pressed', String(on));
      });
    };
    syncPageViewButtons();
    eventBus.on('page-view-settings-changed', syncPageViewButtons);
  }

  // 폭 맞춤·쪽 맞춤은 메뉴/단축키와 같은 커맨드를 탄다 — 계산과 저장 자리가 하나여야 한다.
