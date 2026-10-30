// @ts-nocheck
/**
 * 메모 보기(2026-10-06 사용자 요청 「에디터에서도 메모 볼 수 있나」).
 * 문서에 든 메모(한/글의 검토 메모)를 오른쪽 띠에 작성자, 날짜, 걸린 글, 본문 카드로 보인다. 카드는 한/글처럼 걸린 글과
 * 같은 줄 높이에 놓이고(글과 함께 스크롤, 겹치면 아래로 밀고, 글에서 카드까지 점선), 목록이던 것을 2026-10-21 사용자 요청으로 바꿨다.
 * 본문에서는 메모가 걸린 글의 바탕을 노랗게 칠하고(층 전체를 darken 으로 섞어 글자 색은 그대로, 반투명 덮기는 글씨를 흐렸다. 2026-10-21) 끝에 번호 표를 붙인다. 패널의 메모를 누르면 걸린 글 앞으로 커서와 화면이 가고, 번호 표를 누르거나
 * 커서가 걸린 글 안에 들어가면 패널에서 그 메모가 강조된다. 메모가 있는 문서를 열면 저절로 보이고, 도구 모음 「메모」 단추로
 * 숨긴다(숨긴 것은 기억한다). 새 메모는 오른쪽 클릭 「새 메모」(k-commands.ts, 엔진 insertMemoEx).
 * 카드의 「고치기」, 「지우기」는 엔진 updateMemoBody, deleteMemo(patches/memo-crud-*.rs)를 부른다(2026-10-27 사용자 요청 「메모 CRUD」).
 * 지워도 걸린 글은 남고, 둘 다 스냅샷 하나라 되돌리기 한 번으로 돌아온다. Claude 는 `cli memos add|edit|del` 로 같은 일을 한다.
 *
 * 자료는 엔진 패치 `getMemoList`(patches/memo-list*.rs)에서 온다. 위치는 캐럿 축이라 선택 영역 사각형 API 에 그대로 넣는다.
 * 패치가 없는 WASM(npm 원본)에서는 목록이 비어 단추만 보인다.
 */
import { resolveTarget } from './doc-tools.js';
import { resolveNested, pathAt } from './run-ops.js';

const WIDTH = 300;
const HIDDEN_KEY = 'claude-memo-hidden';
const pad = (n) => String(n).padStart(2, '0');

const CSS = `
.claude-memo-panel{position:fixed;right:0;width:${WIDTH}px;z-index:8900;display:flex;flex-direction:column;box-sizing:border-box;
  background:var(--color-surface-raised,#fff);color:var(--color-text,#222);border-left:1px solid var(--ui-border-light,#ccc);font-size:12px}
.claude-memo-panel header{display:flex;align-items:center;gap:6px;padding:6px 8px;border-bottom:1px solid var(--ui-border-light,#ccc)}
.claude-memo-panel header b{flex:1;font-size:13px}
.claude-memo-panel .close{border:0;background:transparent;color:inherit;font-size:16px;cursor:pointer}
.claude-memo-panel ol{flex:1;position:relative;overflow:hidden;margin:0;padding:0;list-style:none}
.claude-memo-panel li{position:absolute;left:6px;right:6px;box-sizing:border-box;padding:6px 8px;border:1px solid #e6cf7a;border-left:4px solid #e0b020;border-radius:3px;background:#fffbe6;color:#222;cursor:pointer}
.claude-memo-panel li.on{outline:2px solid #d18b00;background:#fff0b3;z-index:1}
.claude-memo-links{position:fixed;left:0;top:0;width:100vw;height:100vh;pointer-events:none;z-index:8899}
.claude-memo-links path{fill:none;stroke:#d18b00;stroke-width:1;stroke-dasharray:3 2;opacity:.7}
.claude-memo-links path.on{stroke:#c0392b;stroke-dasharray:none;opacity:1}
.claude-memo-panel .head{display:flex;gap:6px;align-items:baseline;margin-bottom:3px}
.claude-memo-panel .idx{min-width:10px;height:16px;border-radius:8px;background:#d18b00;color:#fff;font-size:10px;line-height:16px;text-align:center;padding:0 3px}
.claude-memo-panel .who{font-weight:600}
.claude-memo-panel .when,.claude-memo-panel .page{opacity:.65;font-size:11px}
.claude-memo-panel .page{margin-left:auto}
.claude-memo-panel .anchor{opacity:.75;font-size:11px;margin-bottom:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.claude-memo-panel .body{white-space:pre-wrap;word-break:break-word;line-height:1.45;user-select:text}
.claude-memo-panel .empty{padding:12px;opacity:.7}
.claude-memo-panel .acts{display:none;gap:4px}
.claude-memo-panel li:hover .acts,.claude-memo-panel li.on .acts{display:flex}
.claude-memo-panel .acts button{border:1px solid #d9c27a;border-radius:3px;background:#fff;color:#6b5200;font-size:10px;padding:0 5px;cursor:pointer}
.claude-memo-panel .acts button:hover{background:#ffe9a8}
.claude-memo-panel .memo-edit{min-height:54px;border:1px solid #bbb;padding:3px 4px;white-space:pre-wrap;word-break:break-word;line-height:1.45;outline:none;background:var(--color-surface-raised,#fff);user-select:text}
.claude-memo-panel .memo-tools{display:flex;gap:2px;margin-bottom:3px;align-items:center}
.claude-memo-panel .memo-tools button{width:22px;height:20px;padding:0;font-size:12px;cursor:pointer}
.claude-memo-panel .memo-tools input[type=color]{width:24px;height:20px;padding:0;border:1px solid #bbb}
.claude-memo-panel textarea{width:100%;box-sizing:border-box;min-height:54px;font:inherit;line-height:1.45;resize:vertical}
.claude-memo-panel .edit-foot{display:flex;gap:4px;justify-content:flex-end;margin-top:3px}
.claude-memo-layer{position:absolute;left:0;top:0;width:0;height:0;z-index:3;pointer-events:none;mix-blend-mode:darken}
.claude-memo-hl{position:absolute;background:#ffe98a;pointer-events:none}
.claude-memo-hl.on{background:#ffcf5c}
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
  let links = null;   // 걸린 글에서 카드까지 잇는 선(화면 고정 SVG)
  let editing = -1;   // 본문을 고치는 중인 카드. 그동안은 목록을 다시 그리지 않는다(친 글이 날아간다)
  const userHid = () => { try { return localStorage.getItem(HIDDEN_KEY) === '1'; } catch { return false; } };

  // ── 메모 본문 서식 ── 조각 [[{t,cs,bold,italic,underline,strikethrough,textColor}]] 을 그리고, 고친 칸에서 다시 읽는다
  const readRich = (fieldId) => {
    try { return host.read((doc) => (typeof doc.getMemoRich === 'function' ? JSON.parse(doc.getMemoRich(fieldId)) : null)); } catch { return null; }
  };
  const fillRich = (box, rich, fallback) => {
    box.textContent = '';
    if (!rich?.length) { box.textContent = fallback; return; }
    for (const runs of rich) {
      const line = document.createElement('div');
      for (const r of runs) {
        const sp = document.createElement('span');
        sp.textContent = r.t;
        if (r.cs != null) sp.dataset.cs = String(r.cs);
        if (r.bold) sp.style.fontWeight = '700';
        if (r.italic) sp.style.fontStyle = 'italic';
        const deco = [r.underline && 'underline', r.strikethrough && 'line-through'].filter(Boolean).join(' ');
        if (deco) sp.style.textDecorationLine = deco;
        if (r.textColor && r.textColor.toLowerCase() !== '#000000') { sp.style.color = r.textColor; sp.dataset.color = r.textColor; }
        line.append(sp);
      }
      if (!runs.length) line.append(document.createElement('br'));
      box.append(line);
    }
  };
  const cssHex = (c) => {
    const m = String(c).match(/\d+/g);
    return m ? `#${m.slice(0, 3).map((x) => Number(x).toString(16).padStart(2, '0')).join('')}` : '#000000';
  };
  const readEdited = (box) => {
    const base = getComputedStyle(box).color;
    const paras = [];
    const runOf = (node) => {
      const host0 = node.parentElement;
      const cs = getComputedStyle(host0);
      let underline = false, strikethrough = false;
      for (let e = host0; e && e !== box.parentElement; e = e.parentElement) {
        const d = getComputedStyle(e).textDecorationLine;
        if (d.includes('underline') || ['U', 'INS'].includes(e.tagName)) underline = true;
        if (d.includes('line-through') || ['S', 'STRIKE', 'DEL'].includes(e.tagName)) strikethrough = true;
        if (e === box) break;
      }
      const r = { t: node.nodeValue, bold: parseInt(cs.fontWeight, 10) >= 600, italic: cs.fontStyle === 'italic', underline, strikethrough };
      const shape = host0.closest('[data-cs]');
      if (shape) r.cs = Number(shape.dataset.cs);
      if (cs.color !== base) r.textColor = cssHex(cs.color);
      else if (host0.closest('[data-color]')) r.textColor = host0.closest('[data-color]').dataset.color;
      return r;
    };
    const walk = (node, cur) => {
      for (const c of node.childNodes) {
        if (c.nodeType === 3) { if (c.nodeValue) cur.push(runOf(c)); }
        else if (c.nodeName === 'BR') { if (c.nextSibling || !cur.length) { if (c.nextSibling) { paras.push(cur); cur = []; } } }
        else if (['DIV', 'P'].includes(c.nodeName)) {
          if (cur.length) { paras.push(cur); cur = []; }
          const inner = [];
          paras.push(walk(c, inner));
        } else cur = walk(c, cur);
      }
      return cur;
    };
    const last = walk(box, []);
    if (last.length) paras.push(last);
    const same = (a, b) => ['cs', 'bold', 'italic', 'underline', 'strikethrough', 'textColor'].every((k) => a[k] === b[k]);
    return paras.map((runs) => runs.reduce((acc, r) => {
      if (acc.length && same(acc[acc.length - 1], r)) acc[acc.length - 1].t += r.t; else acc.push({ ...r });
      return acc;
    }, []));
  };
  const editRich = (n, rich) => { const m = pick(n); return change('updateMemo', (doc) => doc.updateMemoRich(m.fieldId, JSON.stringify(rich))); };
  /** 메모 본문(at 을 주면 처음 나오는 그 글)에 서식을 얹는다. props: bold, italic, underline, strikethrough, textColor */
  const formatRich = (n, at, props) => {
    const m = pick(n);
    const rich = readRich(m.fieldId);
    if (!rich) throw new Error('메모 서식을 읽지 못함');
    let done = !at;
    const out = rich.map((runs) => runs.flatMap((r) => {
      if (!at) return [{ ...r, ...props }];
      const i = done ? -1 : r.t.indexOf(at);
      if (i < 0) return [r];
      done = true;
      return [{ ...r, t: r.t.slice(0, i) }, { ...r, t: at, ...props }, { ...r, t: r.t.slice(i + at.length) }].filter((x) => x.t);
    }));
    if (!done) throw new Error(`메모 ${n} 본문에 「${at}」 없음`);
    return editRich(n, out);
  };

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

  const setActive = (i) => {
    active = i;
    for (const e of document.querySelectorAll('.claude-memo-hl,.claude-memo-pin,.claude-memo-panel li')) e.classList.toggle('on', Number(e.dataset.i) === i);
    for (const e of links?.querySelectorAll('path') ?? []) e.classList.toggle('on', Number(e.dataset.i) === i);
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
      pin.addEventListener('click', (e) => { e.stopPropagation(); setActive(i); });
      nodes.push(pin);
    });
    layer.replaceChildren(...nodes);
    placeCards();
    setActive(active);
  };

  /** 카드를 걸린 글의 줄 높이에 놓는다. 겹치면 아래로 밀고, 걸린 글 끝에서 카드까지 선을 긋는다 */
  const placeCards = () => {
    const ih = getInputHandler();
    const list = panel?.querySelector('ol');
    if (!list || !ih?.container) return;
    const zoom = ih.viewportManager.getZoom();
    const vs = ih.virtualScroll;
    const c = ih.container;
    const sc = c.querySelector('#scroll-content');
    const cr = c.getBoundingClientRect();
    const lr = list.getBoundingClientRect();
    // 쪽 좌표 → 화면 좌표
    const screen = (r) => ({
      x: cr.left - c.scrollLeft + vs.getPageLeftResolved(r.pageIndex, sc?.clientWidth ?? c.clientWidth) + r.x * zoom,
      y: cr.top - c.scrollTop + vs.getPageOffset(r.pageIndex) + r.y * zoom,
    });
    let bottom = -Infinity;
    const paths = [];
    memos.forEach((m, i) => {
      const card = list.querySelector(`li[data-i="${i}"]`);
      if (!card) return;
      const first = m.rects[0] ?? m.caret;
      const last = m.rects[m.rects.length - 1];
      const tip = last ? screen({ pageIndex: last.pageIndex, x: last.x + last.width, y: last.y }) : first ? screen(first) : null;
      const want = first ? screen(first).y - lr.top - 4 : bottom + 6;   // 자리를 못 잰 메모는 앞 카드 아래
      const top = Math.max(want, bottom + 6);
      card.style.top = `${top}px`;
      bottom = top + card.offsetHeight;
      if (!tip || top > lr.height || bottom < 0) return;
      const y2 = lr.top + top + 10;
      const mid = Math.max(tip.x + 8, cr.right - 12);
      paths.push(`<path data-i="${i}" d="M${tip.x},${tip.y + 2} L${mid},${tip.y + 2} L${lr.left},${y2} L${lr.left + 6},${y2}"/>`);
    });
    if (!links) {
      links = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      links.setAttribute('class', 'claude-memo-links');
      document.body.appendChild(links);
    }
    // 글이 보이는 편집 영역 밖(도구 모음 위 등)으로 선이 새지 않게 자른다
    links.style.clipPath = `inset(${cr.top}px 0 ${Math.max(0, window.innerHeight - cr.bottom)}px 0)`;
    links.innerHTML = paths.join('');
  };

  /** 카드 본문을 고치는 칸으로 바꾼다. Ctrl+Enter 저장, Esc 취소 */
  const startEdit = (li, i) => {
    const m = memos[i];
    editing = i;
    const box = el('div', 'memo-edit');
    box.contentEditable = 'true';
    fillRich(box, m.rich, m.text || '');
    const before = () => JSON.stringify(readEdited(box));
    const start = before();
    const done = (save) => {
      editing = -1;
      const rich = save && before() !== start ? readEdited(box) : null;
      if (rich) editRich(i + 1, rich);
      else refresh();
    };
    // 굵게, 기울임, 밑줄, 취소선, 글자색(한/글 메모처럼 본문에 글자 모양을 준다). Ctrl+B, I, U 는 칸이 스스로 처리한다
    const tools = el('div', 'memo-tools');
    for (const [label, cmd, style] of [['가', 'bold', 'font-weight:700'], ['가', 'italic', 'font-style:italic'], ['가', 'underline', 'text-decoration:underline'], ['가', 'strikeThrough', 'text-decoration:line-through']]) {
      const b = el('button', '', label);
      b.type = 'button';
      b.title = { bold: '굵게(Ctrl+B)', italic: '기울임(Ctrl+I)', underline: '밑줄(Ctrl+U)', strikeThrough: '취소선' }[cmd];
      b.style.cssText = style;
      b.addEventListener('mousedown', (e) => { e.preventDefault(); document.execCommand('styleWithCSS', false, 'true'); document.execCommand(cmd); });
      tools.append(b);
    }
    const color = el('input', '');
    color.type = 'color';
    color.title = '글자색';
    let saved = null;
    color.addEventListener('mousedown', () => { const s = window.getSelection(); saved = s?.rangeCount ? s.getRangeAt(0).cloneRange() : null; });
    color.addEventListener('change', () => {
      const s = window.getSelection();
      box.focus();
      if (saved) { s.removeAllRanges(); s.addRange(saved); }
      document.execCommand('styleWithCSS', false, 'true');
      document.execCommand('foreColor', false, color.value);
    });
    tools.append(color);
    box.addEventListener('paste', (e) => {
      e.preventDefault();
      document.execCommand('insertText', false, e.clipboardData.getData('text/plain'));
    });
    const ok = el('button', '', '저장');
    const cancel = el('button', '', '취소');
    ok.addEventListener('click', () => done(true));
    cancel.addEventListener('click', () => done(false));
    box.addEventListener('keydown', (e) => {
      e.stopPropagation();   // 편집기 단축키가 가로채지 않게
      if (e.key === 'Enter' && e.ctrlKey) { e.preventDefault(); done(true); }
      else if (e.key === 'Escape') { e.preventDefault(); done(false); }
    });
    const foot = el('div', 'edit-foot acts');
    foot.style.display = 'flex';
    foot.append(ok, cancel);
    li.querySelector('.body').replaceWith(tools, box);
    li.append(foot);
    for (const e of [tools, box, foot]) e.addEventListener('click', (ev) => ev.stopPropagation());
    box.addEventListener('input', () => placeCards());   // 칸이 커지면 아래 카드를 민다
    box.focus();
    placeCards();
  };

  const render = () => {
    updateButton();
    if (!panel || editing >= 0) return;
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
      if (canChange()) {
        const acts = el('span', 'acts');
        const fix = el('button', '', '고치기');
        const del = el('button', '', '지우기');
        fix.title = '메모 본문 고치기(Ctrl+Enter 저장, Esc 취소)';
        del.title = '메모 지우기(걸린 글은 남는다. Ctrl+Z 로 되돌린다)';
        fix.addEventListener('click', (e) => { e.stopPropagation(); startEdit(li, i); });
        del.addEventListener('click', (e) => { e.stopPropagation(); remove(i + 1); });
        acts.append(fix, del);
        head.append(acts);
      }
      li.append(head);
      const anchor = m.anchor.replace(/\s+/g, ' ').trim();
      if (anchor) li.append(el('div', 'anchor', `「${anchor}」`));
      const body = el('div', 'body', m.text || '(본문 없음)');
      if (m.text) fillRich(body, m.rich, m.text);
      li.append(body);
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
      m.rich = readRich(m.fieldId);
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
    setActive(i);
    return true;
  };

  // ── 고치기, 지우기, 새로 달기(n 은 패널 번호, 1부터) ─────────────────────
  const canChange = () => host.read((doc) => typeof doc.deleteMemo === 'function');
  /** 스냅샷 하나로 문서를 고친다(되돌리기 한 번). 커서는 제자리 */
  const change = (operationType, fn) => {
    const ih = getInputHandler();
    if (!ih) throw new Error('편집기가 아직 준비되지 않았다');
    const pos = ih.getCursorPosition?.() ?? ih.cursor.getPosition();
    let out;
    ih.executeOperation({ kind: 'snapshot', operationType, operation: (wasm) => { out = JSON.parse(fn(wasm.doc)); return pos; } });
    if (shown) refresh(); else { load(); updateButton(); }
    return out;
  };
  const pick = (n) => {
    load();
    const m = memos[n - 1];
    if (!m) throw new Error(`메모 ${n} 없음(메모 ${memos.length}개)`);
    return m;
  };
  const remove = (n) => { const m = pick(n); return change('deleteMemo', (doc) => doc.deleteMemo(m.fieldId)); };
  const edit = (n, text) => { const m = pick(n); return change('updateMemo', (doc) => doc.updateMemoBody(m.fieldId, text)); };
  /**
   * 좌표(p12, T1r2c1, 표 속 표 T1r2c1/T1r0c0)에 메모를 단다. at 을 주면 그 글이 처음 나오는 문단의 그 글에(칸은 모든 문단에서 찾는다),
   * 없으면 문단 전체에(칸은 첫 문단) 건다
   */
  const add = (ref, text, at, author) => {
    const target = host.read((doc) => {
      const s0 = String(ref).replace(/\s+/g, '');
      if (s0.includes('/')) {
        const x = resolveNested(doc, s0);
        return { s: x.s, para: x.para, path: x.path };
      }
      const pos = resolveTarget(doc, s0);
      if (!pos) throw new Error(`좌표를 못 찾음: ${ref}`);
      if (pos.parentParaIndex == null) return { s: pos.sectionIndex, para: pos.paragraphIndex, path: null, length: pos.length };
      return { s: pos.sectionIndex, para: pos.parentParaIndex, path: [{ controlIndex: pos.controlIndex, cellIndex: pos.cellIndex, cellParaIndex: 0 }] };
    });
    let cellPara = 0, start = 0, end = target.length ?? 0;
    host.read((doc) => {
      if (!target.path) {
        if (!at) return;
        const whole = target.length > 0 ? doc.getTextRange(target.s, target.para, 0, target.length) : '';
        start = whole.indexOf(at);
        if (start < 0) throw new Error(`${ref} 에 「${at}」 없음`);
        end = start + at.length;
        return;
      }
      const pj = (i) => JSON.stringify(pathAt(target.path, i));
      const n = doc.getCellParagraphCountByPath(target.s, target.para, pj(0));
      const lenOf = (i) => doc.getCellParagraphLengthByPath(target.s, target.para, pj(i));
      if (!at) { end = lenOf(0); return; }
      for (let i = 0; i < n; i++) {
        const len = lenOf(i);
        const at0 = len ? doc.getTextInCellByPath(target.s, target.para, pj(i), 0, len).indexOf(at) : -1;
        if (at0 >= 0) { cellPara = i; start = at0; end = at0 + at.length; return; }
      }
      throw new Error(`${ref} 칸의 문단 ${n}개에 「${at}」 없음. 칸 안 표의 글이면 ${ref}/T1r0c0 처럼 적는다`);
    });
    const now = new Date();
    const ft = BigInt(now.getTime() + 11644473600000) * 10000n;   // 작성 시각(k-commands.ts 새 메모와 같은 꼴)
    const r = change('insertMemo', (doc) => doc.insertMemoEx(JSON.stringify({
      sectionIdx: target.s, paraIdx: target.para, start, end, body: text, author: author || 'Claude',
      created: new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().replace(/\.\d+Z$/, 'Z'),
      fileTime: [Number(ft & 0xffffffffn), Number(ft >> 32n)],
      path: target.path ? pathAt(target.path, cellPara).map((e) => [e.controlIndex, e.cellIndex, e.cellParaIndex]) : undefined,
    })));
    if (!shown && !userHid()) show(false);
    return r;
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
    if (i !== active) setActive(i);
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
    let raf = 0;
    sc.addEventListener('scroll', () => { if (shown && !raf) raf = requestAnimationFrame(() => { raf = 0; placeCards(); }); }, { passive: true });
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
    links?.remove();
    links = null;
    dock();
    updateButton();
  };

  // 도구 모음: 「로그 보기」 뒤(없으면 하이퍼링크 단추 뒤)에 「메모」. 메모 수를 함께 보인다
  const updateButton = () => {
    const label = document.querySelector('#tb-claude-memo .tb-label');
    if (label) label.innerHTML = `메모<br/>${memos.length ? `${memos.length}개` : '보기'}`;
    for (const e of document.querySelectorAll('[data-cmd="view:claude-memo"]')) e.classList.toggle('active', shown);
  };
  // 보기 메뉴: 「투명 선」 뒤에 「메모」(2026-10-23 사용자 요청 「메모창을 보고 안 보고 할 메뉴가 없다」). 켜져 있으면 격자 보기처럼 칠한다
  const addMenu = () => {
    const reg = getInputHandler()?.dispatcher?.registry;
    const anchor = document.querySelector('.md-item[data-cmd="view:border-transparent"]');
    if (!reg || !anchor) return false;
    if (!reg.get('view:claude-memo')) {
      reg.register({ id: 'view:claude-memo', label: '메모', canExecute: (ctx) => ctx.hasDocument, execute: () => (shown ? hide(true) : show(true)) });
    }
    if (!document.querySelector('.md-item[data-cmd="view:claude-memo"]')) {
      const item = el('div', 'md-item');
      item.dataset.cmd = 'view:claude-memo';
      item.title = '오른쪽 메모 창 보이기/숨기기';
      item.innerHTML = '<span class="md-icon"></span><span class="md-label">메모</span>';
      anchor.after(item);
    }
    updateButton();
    return true;
  };
  if (!addMenu()) {
    const t = setInterval(() => { if (addMenu()) clearInterval(t); }, 300);
  }
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
  // 메모가 없던 문서에 첫 메모가 생기면(남이 단 메모 포함) 여는 때처럼 패널을 연다
  let firstMemoTimer = null;
  host.events.on('document-mutated', () => {
    if (shown && memos.length) refreshSoon();
    else if (!memos.length) { clearTimeout(firstMemoTimer); firstMemoTimer = setTimeout(onOpen, 400); }
  });
  window.addEventListener('claude-memo-added', () => setTimeout(() => (shown ? refresh() : show(false)), 100));   // 새 메모(k-commands.ts)
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
    add, edit, remove, formatRich,
  };
}
