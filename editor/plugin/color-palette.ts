// @ts-nocheck
/**
 * 글자 색을 색 목록에서 고르게 한다(2026-09-27 사용자 요청). rhwp 는 글자 색 빠른 단추와 글자 모양 대화상자의 색 칸이
 * 운영체제 색 선택기(<input type=color>)만 열어 자주 쓰는 색을 고르기 번거로웠다. 형광펜처럼 목록을 띄운다.
 *   테마 색 10개와 밝게 3단계, 어둡게 2단계 / 표준 색 10개 / 최근 사용한 색(이 PC 에 기억) / 자동(검정), 다른 색...
 */
const THEME = ['#000000', '#ffffff', '#eeece1', '#1f497d', '#4f81bd', '#c0504d', '#9bbb59', '#8064a2', '#4bacc6', '#f79646'];
const STANDARD = ['#c00000', '#ff0000', '#ffc000', '#ffff00', '#92d050', '#00b050', '#00b0f0', '#0070c0', '#002060', '#7030a0'];
const RECENT_KEY = 'claude-hwpx-recent-colors';

const hex = (n) => Math.max(0, Math.min(255, Math.round(n))).toString(16).padStart(2, '0');
const mix = (c, target, t) => {
  const v = [1, 3, 5].map((i) => parseInt(c.slice(i, i + 2), 16));
  return '#' + v.map((x) => hex(x + (target - x) * t)).join('');
};
// 한 열의 단계: 검정은 밝게만, 흰색은 어둡게만
const shades = (c) => {
  if (c === '#000000') return [0.5, 0.35, 0.25, 0.15, 0.05].map((t) => mix(c, 255, t));
  if (c === '#ffffff') return [0.05, 0.15, 0.25, 0.35, 0.5].map((t) => mix(c, 0, t));
  return [mix(c, 255, 0.8), mix(c, 255, 0.6), mix(c, 255, 0.4), mix(c, 0, 0.25), mix(c, 0, 0.5)];
};

const readRecent = () => {
  try { return JSON.parse(localStorage.getItem(RECENT_KEY) || '[]').slice(0, 10); } catch { return []; }
};
export function rememberColor(c) {
  if (!/^#[0-9a-f]{6}$/i.test(c ?? '')) return;
  try {
    const list = [c.toLowerCase(), ...readRecent().filter((x) => x !== c.toLowerCase())].slice(0, 10);
    localStorage.setItem(RECENT_KEY, JSON.stringify(list));
  } catch { /* 저장소가 막혀 있으면 기억하지 않는다 */ }
}

const CSS = `
.claude-cpal{position:fixed;z-index:10050;background:var(--color-surface-raised,#fff);color:var(--color-text,#222);
  border:1px solid var(--ui-border-strong,#999);box-shadow:0 4px 12px rgba(0,0,0,.18);padding:6px;font-size:12px;user-select:none}
.claude-cpal .acts{display:flex;gap:4px;margin-bottom:6px}
.claude-cpal .acts button{flex:1;padding:2px 6px;font-size:12px;cursor:pointer;background:var(--color-surface,#fafafa);
  color:inherit;border:1px solid var(--ui-border-strong,#999)}
.claude-cpal .acts button:hover{background:var(--color-hover-bg,#e8eef8)}
.claude-cpal .lbl{margin:4px 0 2px;opacity:.7}
.claude-cpal .row{display:flex;gap:2px;margin-bottom:2px}
.claude-cpal .grid{display:flex;gap:2px}
.claude-cpal .col{display:flex;flex-direction:column;gap:1px}
.claude-cpal .sw{width:16px;height:16px;box-sizing:border-box;border:1px solid rgba(0,0,0,.2);cursor:pointer}
.claude-cpal .col .sw+.sw{margin-top:0}
.claude-cpal .col .sw:first-child{margin-bottom:3px}
.claude-cpal .sw:hover{outline:2px solid var(--color-text,#222);outline-offset:0}
.claude-cpal .sw.on{outline:2px solid #e07000}`;

let open = null;   // { el, close }

/**
 * anchor 아래에 색 목록을 띄운다. onPick(색) 은 목록에서 고른 색, onOther() 는 「다른 색...」.
 * 목록 안 mousedown 은 기본 동작을 막아 편집 화면의 선택과 포커스를 지킨다.
 */
export function openColorPalette(anchor, { current, onPick, onOther, autoLabel = '자동(검정)', autoColor = '#000000' }) {
  closeColorPalette();
  if (!document.getElementById('claude-cpal-css')) {
    const st = document.createElement('style');
    st.id = 'claude-cpal-css';
    st.textContent = CSS;
    document.head.appendChild(st);
  }
  const cur = (current ?? '').toLowerCase();
  const el = document.createElement('div');
  el.className = 'claude-cpal';
  const pick = (c) => { rememberColor(c); closeColorPalette(); onPick(c); };
  const sw = (c) => {
    const d = document.createElement('div');
    d.className = 'sw' + (c === cur ? ' on' : '');
    d.style.background = c;
    d.title = c;
    d.addEventListener('mousedown', (e) => { e.preventDefault(); e.stopPropagation(); pick(c); });
    return d;
  };

  const acts = document.createElement('div');
  acts.className = 'acts';
  const bAuto = document.createElement('button');
  bAuto.textContent = autoLabel;
  bAuto.addEventListener('mousedown', (e) => { e.preventDefault(); e.stopPropagation(); pick(autoColor); });
  const bOther = document.createElement('button');
  bOther.textContent = '다른 색...';
  bOther.addEventListener('mousedown', (e) => { e.preventDefault(); e.stopPropagation(); closeColorPalette(); onOther?.(); });
  acts.append(bAuto, bOther);
  el.appendChild(acts);

  const lbl = (t) => { const d = document.createElement('div'); d.className = 'lbl'; d.textContent = t; return d; };
  el.appendChild(lbl('테마 색'));
  const grid = document.createElement('div');
  grid.className = 'grid';
  for (const c of THEME) {
    const col = document.createElement('div');
    col.className = 'col';
    col.appendChild(sw(c));
    for (const s of shades(c)) col.appendChild(sw(s));
    grid.appendChild(col);
  }
  el.appendChild(grid);
  el.appendChild(lbl('표준 색'));
  const std = document.createElement('div');
  std.className = 'row';
  for (const c of STANDARD) std.appendChild(sw(c));
  el.appendChild(std);
  const recent = readRecent();
  if (recent.length) {
    el.appendChild(lbl('최근 사용한 색'));
    const rr = document.createElement('div');
    rr.className = 'row';
    for (const c of recent) rr.appendChild(sw(c));
    el.appendChild(rr);
  }
  el.addEventListener('mousedown', (e) => { e.preventDefault(); e.stopPropagation(); });

  document.body.appendChild(el);
  const r = anchor.getBoundingClientRect();
  const w = el.offsetWidth, h = el.offsetHeight;
  el.style.left = Math.max(4, Math.min(r.left, innerWidth - w - 4)) + 'px';
  el.style.top = (r.bottom + 2 + h > innerHeight ? Math.max(4, r.top - h - 2) : r.bottom + 2) + 'px';

  const outside = (e) => { if (!el.contains(e.target) && e.target !== anchor && !anchor.contains(e.target)) closeColorPalette(); };
  const esc = (e) => { if (e.key === 'Escape') { e.stopPropagation(); closeColorPalette(); } };
  setTimeout(() => document.addEventListener('mousedown', outside, true));
  document.addEventListener('keydown', esc, true);
  open = {
    el,
    anchor,
    close() {
      document.removeEventListener('mousedown', outside, true);
      document.removeEventListener('keydown', esc, true);
      el.remove();
    },
  };
}

export function closeColorPalette() {
  if (open) { open.close(); open = null; }
}

const isOpenFor = (anchor) => open?.anchor === anchor;

/** 글자 색 빠른 단추와 글자 모양 대화상자의 색 칸에 색 목록을 붙인다. */
export function installColorPalettes(getInputHandler) {
  // 빠른 단추: rhwp 의 mousedown(운영체제 선택기 열기)보다 먼저 받아 목록을 띄운다
  document.addEventListener('mousedown', (e) => {
    const btn = e.target.closest?.('#btn-text-color');
    if (!btn) return;
    e.preventDefault();
    e.stopImmediatePropagation();
    if (isOpenFor(btn)) { closeColorPalette(); return; }
    const picker = document.getElementById('text-color-picker');
    const bar = document.getElementById('color-bar');
    openColorPalette(btn, {
      current: picker?.value,
      onPick: (c) => {
        if (bar) bar.style.background = c;
        if (picker) picker.value = c;
        getInputHandler()?.eventBus?.emit('format-char', { textColor: c });
      },
      onOther: () => picker?.click(),   // 기존 선택기. 고른 색은 rhwp 의 input 처리기가 적용한다
    });
  }, true);
  document.addEventListener('input', (e) => {
    if (e.target?.id === 'text-color-picker') rememberColor(e.target.value);
  }, true);

  // 글자 모양 대화상자의 색 칸(글자 색, 음영 색, 밑줄 색 등)
  let bypass = null;
  document.addEventListener('click', (e) => {
    const inp = e.target;
    if (!(inp instanceof HTMLInputElement) || inp.type !== 'color' || !inp.closest('.cs-dialog')) return;
    if (bypass === inp) { bypass = null; return; }   // 「다른 색...」으로 연 운영체제 선택기
    e.preventDefault();
    if (isOpenFor(inp)) { closeColorPalette(); return; }
    // 대화상자의 첫 색 칸은 글자 색, 둘째는 음영 색(흰색 = 음영 없음)
    const order = [...inp.closest('.cs-dialog').querySelectorAll('input[type=color]')].indexOf(inp);
    openColorPalette(inp, {
      current: inp.value,
      autoLabel: order === 0 ? '자동(검정)' : order === 1 ? '색 없음' : '검정',
      autoColor: order === 1 ? '#ffffff' : '#000000',
      onPick: (c) => {
        inp.value = c;
        inp.dispatchEvent(new Event('input', { bubbles: true }));
        inp.dispatchEvent(new Event('change', { bubbles: true }));
      },
      onOther: () => {
        try { inp.showPicker(); } catch { bypass = inp; inp.click(); }
      },
    });
  }, true);
  document.addEventListener('change', (e) => {
    const inp = e.target;
    if (inp instanceof HTMLInputElement && inp.type === 'color' && inp.closest('.cs-dialog')) rememberColor(inp.value);
  }, true);
}
