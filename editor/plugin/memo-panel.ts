// @ts-nocheck
/**
 * 메모 보기(2026-10-06 사용자 요청 「에디터에서도 메모 볼 수 있나」).
 * 문서에 든 메모(한/글의 검토 메모)를 오른쪽 패널에 작성자, 날짜, 걸린 글, 본문으로 늘어놓고, 본문에서는 메모가 걸린 글을
 * 노란 바탕으로 칠하고 끝에 번호 표를 붙인다. 패널의 메모를 누르면 걸린 글 앞으로 커서와 화면이 가고, 번호 표를 누르거나
 * 커서가 걸린 글 안에 들어가면 패널에서 그 메모가 강조된다. 메모가 있는 문서를 열면 저절로 보이고, 도구 모음 「메모」 단추로
 * 숨긴다(숨긴 것은 기억한다). 메모는 읽기만 한다 — rhwp 에 메모를 만들거나 고치는 API 가 없다.
 *
 * 자료는 엔진 패치 `getMemoList`(patches/memo-list*.rs)에서 온다. 위치는 캐럿 축이라 선택 영역 사각형 API 에 그대로 넣는다.
 * 패치가 없는 WASM(npm 원본)에서는 목록이 비어 단추만 보인다.
 */
const WIDTH = 300;
const HIDDEN_KEY = 'claude-memo-hidden';
const pad = (n) => String(n).padStart(2, '0');

const CSS = `
.claude-memo-panel{position:fixed;right:0;width:${WIDTH}px;z-index:8900;display:flex;flex-direction:column;box-sizing:border-box;
  background:var(--color-surface-raised,#fff);color:var(--color-text,#222);border-left:1px solid var(--ui-border-light,#ccc);font-size:12px}
.claude-memo-panel header{display:flex;align-items:center;gap:6px;padding:6px 8px;border-bottom:1px solid var(--ui-border-light,#ccc)}
.claude-memo-panel header b{flex:1;font-size:13px}
.claude-memo-panel .close{border:0;background:transparent;color:inherit;font-size:16px;cursor:pointer}
.claude-memo-panel ol{flex:1;overflow:auto;margin:0;padding:6px;list-style:none}
.claude-memo-panel li{margin:0 0 6px;padding:6px 8px;border:1px solid #e6cf7a;border-left:4px solid #e0b020;border-radius:3px;background:#fffbe6;color:#222;cursor:pointer}
.claude-memo-panel li.on{outline:2px solid #d18b00;background:#fff0b3}
.claude-memo-panel .head{display:flex;gap:6px;align-items:baseline;margin-bottom:3px}
.claude-memo-panel .idx{min-width:10px;height:16px;border-radius:8px;background:#d18b00;color:#fff;font-size:10px;line-height:16px;text-align:center;padding:0 3px}
.claude-memo-panel .who{font-weight:600}
.claude-memo-panel .when,.claude-memo-panel .page{opacity:.65;font-size:11px}
.claude-memo-panel .page{margin-left:auto}
.claude-memo-panel .anchor{opacity:.75;font-size:11px;margin-bottom:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.claude-memo-panel .body{white-space:pre-wrap;word-break:break-word;line-height:1.45;user-select:text}
.claude-memo-panel .empty{padding:12px;opacity:.7}
.claude-memo-layer{position:absolute;left:0;top:0;width:0;height:0;z-index:3;pointer-events:none}
.claude-memo-hl{position:absolute;background:rgba(255,205,40,.38);mix-blend-mode:multiply;pointer-events:none}
.claude-memo-hl.on{background:rgba(255,150,0,.5)}
.claude-memo-pin{position:absolute;min-width:8px;height:14px;padding:0 3px;border:0;border-radius:7px;background:#d18b00;color:#fff;
  font:700 9px/14px sans-serif;text-align:center;cursor:pointer;pointer-events:auto;box-shadow:0 0 0 1px #fff}
.claude-memo-pin.on{background:#c0392b}`;

/**
 * 작성 일시(지역 시각). CreateDateTime 의 숫자를 그대로 쓴다 — 한/글은 끝에 Z 를 붙이지만 값은 지역 시각이다
 * (2026-10-06 실측: Command 의 FILETIME 05:13:01 UTC 인 메모가 `14:13:01Z` 로 적혀 있다. UTC 로 읽으면 9시간 늦어진다).
 * 값이 깨졌으면(python-hwpx 메모를 한/글이 다시 저장하면 7887년이 나온다) Command 의 FILETIME 을 쓰고, 그것도 깨졌으면 비운다.
 */
function memoDate(createdAt, command) {
  const saneYear = (y) => y >= 1990 && y <= 2100;
  const m = /^(\d{4})-(\d\d)-(\d\d)[T ](\d\d):(\d\d)/.exec(createdAt || '');
  if (m && saneYear(Number(m[1]))) return `${m[1]}-${m[2]}-${m[3]} ${m[4]}:${m[5]}`;
  // MEMO/<모양>/<번호>/<FILETIME 하위 32비트>/<상위 32비트>/<작성자>/
  const [lo, hi] = String(command || '').split('/').slice(3, 5).map(Number);
  const d = Number.isFinite(lo) && Number.isFinite(hi) && hi > 0 ? new Date((hi * 4294967296 + lo) / 10000 - 11644473600000) : null;
  return d && !Number.isNaN(d.getTime()) && saneYear(d.getFullYear())
    ? `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}` : '';
}

const el = (tag, cls, text) => {
  const e = document.createElement(tag);
  e.className = cls;
  if (text != null) e.textContent = text;
  return e;
};

export function installMemoPanel(host, getInputHandler) {
  let memos = [];
  let shown = false;
  let panel = null;
  let layer = null;
  let active = -1;
  let refreshTimer = null;
  let watched = null;
  const userHid = () => { try { return localStorage.getItem(HIDDEN_KEY) === '1'; } catch { return false; } };

  const readRaw = () => {
    try { return host.read((doc) => (typeof doc.getMemoList === 'function' ? JSON.parse(doc.getMemoList()) : [])); } catch { return []; }
  };
  /** 칸 경로(마지막 칸의 문단을 para 로). 스튜디오 커서와 경로 API 가 쓰는 꼴이다 */
  const cellPath = (m, para) => m.path.map((h, k) => ({ controlIndex: h.controlIndex, cellIndex: h.cellIndex, cellParaIndex: k === m.path.length - 1 ? para : h.cellParaIndex }));
  const isPoint = (m) => !m.closed || (m.startPara === m.endPara && m.startOffset === m.endOffset);

  /** 걸린 글의 줄별 사각형(쪽 좌표). 범위가 없으면 그 자리의 캐럿 사각형 */
  const measure = (m) => {
    const w = getInputHandler()?.wasm;
    m.rects = [];
    m.caret = null;
    if (!w) return;
    try {
      if (!m.path.length) {
        if (isPoint(m)) m.caret = w.getCursorRect(m.sectionIndex, m.startPara, m.startOffset);
        else m.rects = w.getSelectionRects(m.sectionIndex, m.startPara, m.startOffset, m.endPara, m.endOffset);
      } else if (!m.path.some((h) => h.textbox)) {
        const path = JSON.stringify(cellPath(m, m.startPara));
        if (isPoint(m)) m.caret = w.getCursorRectByPath(m.sectionIndex, m.paraIndex, path, m.startOffset);
        else m.rects = w.getSelectionRectsInCellByPath(m.sectionIndex, m.paraIndex, path, m.startPara, m.startOffset, m.endPara, m.endOffset);
      }
    } catch { /* 자리를 못 재는 메모(글상자 안 등)는 패널에만 보인다 */ }
  };

  const setActive = (i, scrollCard) => {
    active = i;
    for (const e of document.querySelectorAll('.claude-memo-hl,.claude-memo-pin,.claude-memo-panel li')) e.classList.toggle('on', Number(e.dataset.i) === i);
    if (scrollCard && i >= 0) panel?.querySelector(`li[data-i="${i}"]`)?.scrollIntoView({ block: 'nearest' });
  };

  /** 본문 위 덧그리기: 걸린 글 바탕과 번호 표 */
  const place = () => {
    const ih = getInputHandler();
    const sc = ih?.container?.querySelector('#scroll-content');
    if (!shown || !sc || !memos.length) { layer?.remove(); layer = null; return; }
    if (!layer || layer.parentElement !== sc) {
      layer?.remove();
      layer = el('div', 'claude-memo-layer');
      sc.appendChild(layer);
    }
    const zoom = ih.viewportManager.getZoom();
    const vs = ih.virtualScroll;
    const at = (r) => ({ left: vs.getPageLeftResolved(r.pageIndex, sc.clientWidth) + r.x * zoom, top: vs.getPageOffset(r.pageIndex) + r.y * zoom });
    const nodes = [];
    memos.forEach((m, i) => {
      for (const r of m.rects) {
        const p = at(r);
        const hl = el('div', 'claude-memo-hl');
        hl.dataset.i = String(i);
        hl.style.cssText = `left:${p.left}px;top:${p.top}px;width:${r.width * zoom}px;height:${r.height * zoom}px`;
        nodes.push(hl);
      }
      const last = m.rects[m.rects.length - 1];
      const tip = last ? { pageIndex: last.pageIndex, x: last.x + last.width, y: last.y } : m.caret;
      if (!tip) return;
      const p = at(tip);
      const pin = el('button', 'claude-memo-pin', String(i + 1));
      pin.dataset.i = String(i);
      pin.title = `${m.author || '메모'}: ${m.text.slice(0, 80)}`;
      pin.style.cssText = `left:${p.left - 3}px;top:${p.top - 9}px`;
      pin.addEventListener('mousedown', (e) => { e.preventDefault(); e.stopPropagation(); });   // 본문 포커스와 캐럿을 그대로 둔다
      pin.addEventListener('click', (e) => { e.stopPropagation(); setActive(i, true); });
      nodes.push(pin);
    });
    layer.replaceChildren(...nodes);
    setActive(active);
  };

  const render = () => {
    updateButton();
    if (!panel) return;
    panel.querySelector('.count').textContent = memos.length ? `${memos.length}개` : '';
    const list = panel.querySelector('ol');
    if (!memos.length) { list.replaceChildren(el('div', 'empty', '이 문서에는 메모가 없다.')); return; }
    list.replaceChildren(...memos.map((m, i) => {
      const li = el('li', '');
      li.dataset.i = String(i);
      li.title = '누르면 메모가 걸린 글로 간다';
      const head = el('div', 'head');
      head.append(el('span', 'idx', String(i + 1)), el('span', 'who', m.author || '작성자 없음'), el('span', 'when', m.when));
      if (m.page) head.append(el('span', 'page', `${m.page}쪽`));
      li.append(head);
      const anchor = m.anchor.replace(/\s+/g, ' ').trim();
      if (anchor) li.append(el('div', 'anchor', `「${anchor}」`));
      li.append(el('div', 'body', m.text || '(본문 없음)'));
      // 본문 글을 끌어서 고르는 중이면(복사하려는 것) 옮겨 가지 않는다
      li.addEventListener('click', () => { if (!String(window.getSelection?.() ?? '')) go(i); });
      return li;
    }));
  };

  /** 메모를 다시 읽고 자리를 잰다. 문서 순서(쪽, 세로, 가로)로 번호를 매긴다 */
  const load = () => {
    let near = { page: 0, y: 0, x: 0 };
    memos = readRaw().map((r, seq) => {
      const m = { ...r, seq, author: r.author || String(r.command || '').split('/')[5] || '', when: memoDate(r.createdAt, r.command) };
      measure(m);
      const first = m.rects[0] ?? m.caret;
      if (first) near = { page: first.pageIndex, y: first.y, x: first.x };
      m.key = near;                                  // 자리를 못 잰 메모는 앞 메모 곁에 둔다
      m.page = first ? first.pageIndex + 1 : 0;
      return m;
    }).sort((a, b) => (a.key.page - b.key.page) || (a.key.y - b.key.y) || (a.key.x - b.key.x) || (a.seq - b.seq));
    if (active >= memos.length) active = -1;
  };
  const refresh = () => {
    load();
    render();
    place();
  };
  const refreshSoon = (ms = 400) => {
    clearTimeout(refreshTimer);
    refreshTimer = setTimeout(() => { if (shown) refresh(); }, ms);
  };
  const placeSoon = () => { requestAnimationFrame(place); setTimeout(place, 200); };

  const posOf = (m, para, charOffset) => {
    if (!m.path.length) return { sectionIndex: m.sectionIndex, paragraphIndex: para, charOffset };
    const path = cellPath(m, para);
    return {
      sectionIndex: m.sectionIndex, paragraphIndex: m.paraIndex, charOffset,
      parentParaIndex: m.paraIndex, controlIndex: path[0].controlIndex, cellIndex: path[0].cellIndex, cellParaIndex: path[0].cellParaIndex,
      ...(path.length > 1 ? { cellPath: path } : {}),
      ...(m.path[0].textbox ? { isTextBox: true } : {}),
    };
  };
  /** 메모가 걸린 글 앞으로 커서와 화면을 옮긴다. 글을 선택하지는 않는다(선택한 채 치면 걸린 글이 지워진다) */
  const go = (i) => {
    const m = memos[i];
    const ih = getInputHandler();
    if (!m || !ih) return false;
    try {
      ih.exitFootnoteModeForBodyNavigation?.();
      ih.cursor.clearSelection();
      ih.cursor.moveTo(posOf(m, m.startPara, m.startOffset));
      ih.cursor.resetPreferredX?.();
      ih.active = true;
      ih.updateCaret(true);
      ih.focusTextarea();
    } catch { /* 캐럿을 놓지 못하는 자리(글상자 안 등)는 화면만 옮긴다 */ }
    const first = m.rects[0] ?? m.caret;
    if (first) {
      const c = ih.container;
      const y = ih.virtualScroll.getPageOffset(first.pageIndex) + first.y * ih.viewportManager.getZoom();
      c.scrollTop = Math.max(0, Math.min(c.scrollHeight - c.clientHeight, y - c.clientHeight / 3));
    }
    setActive(i, true);
    return true;
  };

  /** 커서 자리가 메모가 걸린 글 안인가 */
  const covers = (m, pos) => {
    if (!m || isPoint(m) || pos.sectionIndex !== m.sectionIndex) return false;
    let para;
    if (!m.path.length) {
      if (pos.parentParaIndex != null) return false;
      para = pos.paragraphIndex;
    } else {
      if (pos.parentParaIndex !== m.paraIndex) return false;
      const p = pos.cellPath?.length ? pos.cellPath : [{ controlIndex: pos.controlIndex, cellIndex: pos.cellIndex, cellParaIndex: pos.cellParaIndex }];
      if (p.length !== m.path.length) return false;
      for (let k = 0; k < p.length; k++) {
        if (p[k].controlIndex !== m.path[k].controlIndex || p[k].cellIndex !== m.path[k].cellIndex) return false;
        if (k < p.length - 1 && p[k].cellParaIndex !== m.path[k].cellParaIndex) return false;
      }
      para = p[p.length - 1].cellParaIndex;
    }
    if (para < m.startPara || para > m.endPara) return false;
    if (para === m.startPara && pos.charOffset < m.startOffset) return false;
    return !(para === m.endPara && pos.charOffset > m.endOffset);
  };
  /** 커서가 걸린 글 안에 있는 메모. 지금 강조한 메모가 맞으면 그대로 둔다(범위가 맞닿은 메모 사이에서 튀지 않게) */
  const memoAt = (pos) => (covers(memos[active], pos) ? active : memos.findIndex((m) => covers(m, pos)));
  host.events.on('cursor-rect-updated', () => {
    if (!shown || !memos.length) return;
    const pos = getInputHandler()?.getCursorPosition?.();
    const i = pos ? memoAt(pos) : -1;
    if (i !== active) setActive(i, true);
  });

  /** 패널을 편집 영역 오른쪽에 붙이고 그만큼 편집 영역을 줄인다(쪽을 가리지 않게) */
  const dock = () => {
    const area = document.getElementById('editor-area');
    if (!area) return;
    area.style.marginRight = shown ? `${WIDTH}px` : '';
    if (!panel) return;
    const r = area.getBoundingClientRect();
    panel.style.top = `${r.top}px`;
    panel.style.bottom = `${Math.max(0, window.innerHeight - r.bottom)}px`;
  };
  /** 쪽 배치가 바뀌는 때(창 크기, 패널 여닫기)에 덧그리기를 다시 놓는다 */
  const watchResize = () => {
    const sc = getInputHandler()?.container;
    if (!sc || watched === sc) return;
    watched = sc;
    new ResizeObserver(() => { dock(); placeSoon(); }).observe(sc);
  };

  const show = (byUser) => {
    if (byUser) { try { localStorage.removeItem(HIDDEN_KEY); } catch { /* 저장소 없음 */ } }
    if (shown) return;
    shown = true;
    if (!document.getElementById('claude-memo-css')) {
      const st = el('style', '', CSS);
      st.id = 'claude-memo-css';
      document.head.appendChild(st);
    }
    panel = el('div', 'claude-memo-panel');
    panel.innerHTML = '<header><b>메모 <span class="count"></span></b><button class="close" title="메모 숨기기">×</button></header><ol></ol>';
    panel.querySelector('.close').addEventListener('click', () => hide(true));
    document.body.appendChild(panel);
    dock();
    watchResize();
    refresh();
    placeSoon();
  };
  const hide = (byUser) => {
    if (byUser) { try { localStorage.setItem(HIDDEN_KEY, '1'); } catch { /* 저장소 없음 */ } }
    shown = false;
    panel?.remove();
    panel = null;
    layer?.remove();
    layer = null;
    dock();
    updateButton();
  };

  // 도구 모음: 「로그 보기」 뒤(없으면 하이퍼링크 단추 뒤)에 「메모」. 메모 수를 함께 보인다
  const updateButton = () => {
    const label = document.querySelector('#tb-claude-memo .tb-label');
    if (label) label.innerHTML = `메모<br/>${memos.length ? `${memos.length}개` : '보기'}`;
  };
  const addButton = () => {
    if (document.getElementById('tb-claude-memo')) return true;
    const anchor = document.getElementById('tb-claude-log') ?? [...document.querySelectorAll('.tb-btn')].find((b) => b.title === '하이퍼링크');
    if (!anchor) return false;
    const btn = el('button', 'tb-btn');
    btn.id = 'tb-claude-memo';
    btn.title = '메모 보기/숨기기(문서에 달린 검토 메모)';
    btn.innerHTML = '<span class="tb-icon-text">▤</span><span class="tb-label">메모<br/>보기</span>';
    btn.addEventListener('mousedown', (e) => e.preventDefault());   // 본문 포커스를 빼앗지 않는다
    btn.addEventListener('click', () => (shown ? hide(true) : show(true)));
    anchor.after(btn);
    updateButton();
    return true;
  };
  if (!addButton()) {
    const t = setInterval(() => { if (addButton()) clearInterval(t); }, 300);
  }

  // 문서를 열면: 메모가 있으면 보이고(사용자가 숨겨 두지 않았다면), 없으면 패널을 접는다
  const onOpen = () => {
    const count = readRaw().length;
    if (!count) {
      memos = [];
      if (shown) hide(false); else updateButton();
    } else if (shown) refresh();
    else if (!userHid()) show(false);
    else { load(); updateButton(); }
  };
  host.onDocumentSwap(() => setTimeout(onOpen, 300));
  setTimeout(onOpen, 600);
  host.events.on('document-mutated', () => { if (shown && memos.length) refreshSoon(); });
  host.events.on('document-layout-refreshed', () => { if (shown && memos.length) refreshSoon(200); });
  for (const name of ['zoom-changed', 'page-view-settings-changed', 'viewport-resize']) host.events.on(name, () => { if (shown) placeSoon(); });

  return {
    /** Claude 용(`$E memos`): 문서 순서의 메모 목록 */
    list() {
      if (shown) refresh();
      else { load(); updateButton(); }               // 숨겨 둔 채로도 같은 번호로 읽는다
      return memos.map((m, i) => ({
        n: i + 1, author: m.author, when: m.when, page: m.page, anchor: m.anchor, text: m.text,
        sectionIndex: m.sectionIndex, paraIndex: m.paraIndex, path: m.path, startPara: m.startPara, endPara: m.endPara,
      }));
    },
    /** n 번째 메모가 걸린 글로 사용자 화면을 옮긴다 */
    go(n) {
      if (!shown) show(false);
      return go(n - 1);
    },
  };
}
