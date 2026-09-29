// ==== find ====
    // 본문과의 배치 (아이콘 버튼 5개) + 본문 위치 드롭다운
    const wrapRow = this.row();
    wrapRow.classList.add('pp-pos-detail');
    wrapRow.appendChild(this.label('본문과의 배치:'));
    const wrapIcons = ['⬒', '⬓', '⬔', '⬕', '⬖'];
    const wrapTitles = ['자리 차지', '어울림', '빈 공간 채움', '글 뒤로', '글 앞으로'];
    this.wrapBtns = [];
    wrapTitles.forEach((title, i) => {
      const btn = document.createElement('button');
      btn.className = 'pp-wrap-btn';
      btn.textContent = wrapIcons[i];
      btn.title = title;
      btn.addEventListener('click', () => this.selectWrap(i));
      wrapRow.appendChild(btn);
      this.wrapBtns.push(btn);
    });
    // 본문 위치(P)
    wrapRow.appendChild(this.label('본문 위치(P):'));
// ==== replace ====
    // 본문과의 배치 (글자 단추 5개), 다음 줄에 본문 위치 드롭다운
    let wrapRow = this.row();
    wrapRow.classList.add('pp-pos-detail');
    wrapRow.appendChild(this.label('본문과의 배치:'));
    // [claude-hwpx wrap-text-labels] 아이콘(⬒⬓⬔⬕⬖)만으로는 뜻을 알 수 없다는 사용자 지적(2026-09-29) — 글자로 보인다.
    // 글자 단추는 넓어 「본문 위치」를 다음 줄로 내린다(한 줄에 두면 이름표가 꺾이고 가로 스크롤이 생겼다)
    const wrapTitles = ['자리 차지', '어울림', '빈 공간 채움', '글 뒤로', '글 앞으로'];
    this.wrapBtns = [];
    wrapTitles.forEach((title, i) => {
      const btn = document.createElement('button');
      btn.className = 'pp-wrap-btn';
      btn.textContent = title;
      btn.style.width = 'auto';
      btn.style.padding = '0 8px';
      btn.style.whiteSpace = 'nowrap';
      btn.title = title;
      btn.addEventListener('click', () => this.selectWrap(i));
      wrapRow.appendChild(btn);
      this.wrapBtns.push(btn);
    });
    posFs.appendChild(wrapRow);
    this.posDetailEls.push(wrapRow);
    // 본문 위치(P)
    wrapRow = this.row();
    wrapRow.classList.add('pp-pos-detail');
    wrapRow.appendChild(this.label('본문 위치(P):'));
