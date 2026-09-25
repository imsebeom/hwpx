// @ts-nocheck
/**
 * 「로그 보기」 도구 모음 단추와 오른쪽 패널. Claude 가 `changes`(실시간 편집 기록)와 `log`(작업 기록)로 읽는 것과
 * 같은 줄을 서버 `/api/logview` 에서 받아 보인다(줄 만들기는 editor/log-format.mjs 한 곳). 열려 있는 동안 2초마다 새로 받는다.
 */
export function installLogPanel() {
  let panel = null;
  let timer = null;
  let tab = 'ops';
  let withClaude = true;

  const css = `
.claude-log-panel{position:fixed;top:0;right:0;bottom:0;width:440px;z-index:9000;display:flex;flex-direction:column;
  background:var(--color-surface-raised,#fff);color:var(--color-text,#222);border-left:1px solid var(--ui-border-light,#ccc);
  box-shadow:-4px 0 12px rgba(0,0,0,.12);font-size:12px}
.claude-log-panel header{display:flex;align-items:center;gap:6px;padding:6px 8px;border-bottom:1px solid var(--ui-border-light,#ccc)}
.claude-log-panel header b{flex:1;font-size:13px}
.claude-log-panel .tabs button{border:1px solid var(--ui-border-light,#ccc);background:transparent;color:inherit;padding:2px 8px;cursor:pointer}
.claude-log-panel .tabs button.on{background:var(--ui-hover,#e8eef8);font-weight:600}
.claude-log-panel .close{border:0;background:transparent;color:inherit;font-size:16px;cursor:pointer}
.claude-log-panel .opts{display:flex;gap:10px;align-items:center;padding:4px 8px;border-bottom:1px solid var(--ui-border-light,#ccc);opacity:.85}
.claude-log-panel ol{flex:1;overflow:auto;margin:0;padding:4px 8px;list-style:none;font-family:Consolas,'D2Coding',monospace;white-space:pre-wrap;word-break:break-all}
.claude-log-panel li{padding:2px 0;border-bottom:1px dotted var(--ui-border-light,#ddd)}
.claude-log-panel li.claude{color:#6a3fb5}
.claude-log-panel li.undo{opacity:.6}
.claude-log-panel .foot{padding:4px 8px;border-top:1px solid var(--ui-border-light,#ccc);opacity:.7}`;

  const render = (data) => {
    if (!panel) return;
    const list = panel.querySelector('ol');
    const atBottom = list.scrollTop + list.clientHeight >= list.scrollHeight - 8;
    const rows = tab === 'ops'
      ? data.ops.filter((o) => withClaude || o.src !== 'claude')
      : data.work;
    list.replaceChildren(...rows.map((r) => {
      const li = document.createElement('li');
      li.textContent = r.src === 'claude' ? `Claude · ${r.text}` : r.text;
      if (r.src === 'claude') li.classList.add('claude');
      if (r.act === 'undo') li.classList.add('undo');
      if (r.act === 'mark') li.style.cssText = 'font-weight:600;border-bottom:1px solid;margin-top:6px';
      return li;
    }));
    if (!rows.length) {
      const li = document.createElement('li');
      li.textContent = tab === 'ops' ? '아직 편집 기록이 없다.' : '작업 기록이 없다.';
      list.appendChild(li);
    }
    panel.querySelector('.foot').textContent =
      `${rows.length}줄 · ${data.doc ? data.doc.split(/[\\/]/).pop() : ''} · ${new Date().toTimeString().slice(0, 8)} 갱신`;
    if (atBottom) list.scrollTop = list.scrollHeight;
  };
  /** 메뉴, 도구 모음, 서식 막대 아래에서 시작한다(단추를 가리지 않게. 도구 모음을 접고 펴도 따라간다) */
  const placeBelowBars = () => {
    if (!panel) return;
    const bars = ['#menu-bar', '#icon-toolbar', '#style-bar'].map((s) => document.querySelector(s)).filter(Boolean);
    panel.style.top = `${Math.max(0, ...bars.map((b) => b.getBoundingClientRect().bottom))}px`;
  };
  const load = async () => {
    placeBelowBars();
    try { render(await (await fetch('/api/logview?limit=800')).json()); } catch { /* 서버가 잠시 없으면 다음 주기에 */ }
  };

  const open = () => {
    if (!document.getElementById('claude-log-css')) {
      const st = document.createElement('style');
      st.id = 'claude-log-css';
      st.textContent = css;
      document.head.appendChild(st);
    }
    panel = document.createElement('div');
    panel.className = 'claude-log-panel';
    panel.innerHTML = `
      <header><b>로그</b>
        <span class="tabs"><button data-t="ops">편집 기록</button><button data-t="work">작업 기록</button></span>
        <button class="close" title="닫기">×</button></header>
      <div class="opts"><label><input type="checkbox" class="with-claude"> Claude 편집도 보기</label>
        <span>편집 기록 = Claude 가 changes 로 읽는 줄</span></div>
      <ol></ol><div class="foot"></div>`;
    const setTab = (t) => {
      tab = t;
      panel.querySelectorAll('.tabs button').forEach((b) => b.classList.toggle('on', b.dataset.t === t));
      panel.querySelector('.opts').style.display = t === 'ops' ? '' : 'none';
      load();
    };
    panel.querySelectorAll('.tabs button').forEach((b) => b.addEventListener('click', () => setTab(b.dataset.t)));
    const cb = panel.querySelector('.with-claude');
    cb.checked = withClaude;
    cb.addEventListener('change', () => { withClaude = cb.checked; load(); });
    panel.querySelector('.close').addEventListener('click', close);
    placeBelowBars();
    document.body.appendChild(panel);
    setTab(tab);
    timer = setInterval(load, 2000);
  };
  const close = () => {
    clearInterval(timer);
    timer = null;
    panel?.remove();
    panel = null;
  };
  const toggle = () => (panel ? close() : open());

  // 도구 모음: 하이퍼링크 단추 뒤(없으면 도구 모음 끝)에 「로그 보기」
  const addButton = () => {
    if (document.getElementById('tb-claude-log')) return true;
    const anchor = [...document.querySelectorAll('.tb-btn')].find((b) => b.title === '하이퍼링크');
    const bar = anchor?.parentElement ?? document.querySelector('.tb-btn')?.parentElement;
    if (!bar) return false;
    const btn = document.createElement('button');
    btn.className = 'tb-btn';
    btn.id = 'tb-claude-log';
    btn.title = '로그 보기(Claude 가 읽는 편집 기록)';
    btn.innerHTML = '<span class="tb-icon-text">≣</span><span class="tb-label">로그<br/>보기</span>';
    btn.addEventListener('mousedown', (e) => e.preventDefault());   // 본문 포커스를 빼앗지 않는다
    btn.addEventListener('click', toggle);
    if (anchor) anchor.after(btn); else bar.appendChild(btn);
    return true;
  };
  if (!addButton()) {
    const t = setInterval(() => { if (addButton()) clearInterval(t); }, 300);
  }
}
