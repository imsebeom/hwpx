// ==== find ====
  // 폭 맞춤·쪽 맞춤은 메뉴/단축키와 같은 커맨드를 탄다 — 계산과 저장 자리가 하나여야 한다.
// ==== replace ====
  // [claude-hwpx page-view-buttons] 한 쪽, 두 쪽, 자동 보기 단추를 폭 맞춤 앞에 둔다(명령은 page-view-cmd).
  // 단추는 그림 대신 글자(한 쪽, 두 쪽, 자동, 폭 맞춤, 쪽 맞춤, 사용자 요청 2026-10-25)이고, 지금 배치에 맞는 단추를 눌린 모양으로 보인다
  {
    const fitWidth = document.getElementById('sb-zoom-fit-width')!;
    for (const [id, label] of [['sb-zoom-fit-width', '폭 맞춤'], ['sb-zoom-fit', '쪽 맞춤']]) {
      const btn = document.getElementById(id)!;
      btn.classList.add('stb-text-btn');
      btn.textContent = label;
    }
    const group = document.createElement('span');
    group.className = 'stb-page-view-group';
    const buttons: HTMLButtonElement[] = [];
    for (const n of [1, 2, 0]) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'stb-icon-btn stb-text-btn stb-page-view-btn';
      btn.title = n === 0 ? '자동 쪽 보기' : `${['한', '두'][n - 1]} 쪽 보기`;
      btn.setAttribute('aria-label', btn.title);
      btn.textContent = n === 0 ? '자동' : `${['한', '두'][n - 1]} 쪽`;
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
