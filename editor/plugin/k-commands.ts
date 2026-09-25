// @ts-nocheck
/**
 * Ctrl+K 계열 중 rhwp 에 없던 넣기 기능(한/글 「입력」 메뉴와 같게).
 *   Ctrl+K,H 하이퍼링크 / Ctrl+K,R 상호 참조(책갈피 쪽 번호) / Ctrl+K,D 날짜/시간 문자열
 *   Ctrl+K,C 날짜/시간 코드 / Ctrl+K,F 날짜/시간 형식(골라서 문자열로 넣고 기본 형식으로 기억)
 * 필드는 엔진 패치 insertFieldEx(patches/field-ex-*.rs)로 넣고, 매개변수는 한/글이 쓴 HWPX 원문과 같은 모양으로 만든다
 * (하이퍼링크, 상호 참조는 rhwp 시료의 한/글 파일, 날짜 코드는 한/글 COM 으로 만든 파일에서 확인, 2026-09-26).
 * 모든 넣기는 스냅샷 하나라 되돌리기 한 번으로 취소된다.
 */

const FORMATS = [
  ['ymd', '2026년 9월 26일'],
  ['ymdw', '2026년 9월 26일 토요일'],
  ['dot', '2026. 9. 26.'],
  ['iso', '2026-09-26'],
  ['full', '2026년 9월 26일 토요일 오전 6:47:13'],
  ['time', '오전 6:47'],
];
const DAYS = ['일요일', '월요일', '화요일', '수요일', '목요일', '금요일', '토요일'];
const FMT_KEY = 'hwpx-editor.dateFormat';

function formatDate(d, key) {
  const y = d.getFullYear(), m = d.getMonth() + 1, day = d.getDate(), w = DAYS[d.getDay()];
  const h = d.getHours(), ap = h < 12 ? '오전' : '오후', h12 = h % 12 === 0 ? 12 : h % 12;
  const mm = String(d.getMinutes()).padStart(2, '0'), ss = String(d.getSeconds()).padStart(2, '0');
  switch (key) {
    case 'ymdw': return `${y}년 ${m}월 ${day}일 ${w}`;
    case 'dot': return `${y}. ${m}. ${day}.`;
    case 'iso': return `${y}-${String(m).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    case 'full': return `${y}년 ${m}월 ${day}일 ${w} ${ap} ${h12}:${mm}:${ss}`;
    case 'time': return `${ap} ${h12}:${mm}`;
    default: return `${y}년 ${m}월 ${day}일`;
  }
}
const savedFormat = () => { try { return localStorage.getItem(FMT_KEY) || 'ymd'; } catch { return 'ymd'; } };
const xml = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const hwpEsc = (s) => String(s).replace(/([\\:;])/g, '\\$1');

/** 커서(또는 한 문단 안 선택)의 자리 */
function place(ih) {
  const pos = ih.getCursorPosition?.();
  if (!pos) return null;
  const sel = ih.cursor?.getSelectionOrdered?.();
  const inCell = pos.parentParaIndex !== undefined;
  const path = inCell
    ? (pos.cellPath?.length ? pos.cellPath : [{ controlIndex: pos.controlIndex, cellIndex: pos.cellIndex, cellParaIndex: pos.cellParaIndex ?? 0 }])
    : null;
  let start = pos.charOffset, end = pos.charOffset;
  if (sel) {
    const same = inCell
      ? JSON.stringify(sel.start.cellPath ?? null) === JSON.stringify(sel.end.cellPath ?? null) && sel.start.cellIndex === sel.end.cellIndex
      : sel.start.paragraphIndex === sel.end.paragraphIndex;
    if (same) { start = sel.start.charOffset; end = sel.end.charOffset; }
  }
  return { pos, inCell, path, sec: pos.sectionIndex, para: inCell ? pos.parentParaIndex : pos.paragraphIndex, start, end };
}

export function installKCommands(host, getInputHandler) {
  /** 자리 p 의 글 조작(본문/셀) */
  const ops = (doc, p) => {
    const pj = p.path && JSON.stringify(p.path);
    return {
      text: (s, e) => {
        if (e <= s) return '';
        if (!p.inCell) return doc.getTextRange(p.sec, p.para, s, e - s);
        const c = p.path[p.path.length - 1];
        return p.path.length === 1 ? doc.getTextInCell(p.sec, p.para, c.controlIndex, c.cellIndex, c.cellParaIndex, s, e - s) : '';
      },
      del: (s, n) => (n <= 0 ? null : p.inCell ? doc.deleteTextInCellByPath(p.sec, p.para, pj, s, n) : doc.deleteText(p.sec, p.para, s, n)),
      ins: (s, t) => (p.inCell ? doc.insertTextInCellByPath(p.sec, p.para, pj, s, t) : doc.insertText(p.sec, p.para, s, t)),
      field: (s, kind, t, params) => JSON.parse(doc.insertFieldEx(JSON.stringify({
        sectionIdx: p.sec, paraIdx: p.para, charOffset: s, kind, text: t, params,
        path: p.inCell ? p.path.map((c) => [c.controlIndex, c.cellIndex, c.cellParaIndex]) : undefined,
      }))),
      charFmt: (s, e, props) => {
        if (!p.inCell) return doc.applyCharFormat(p.sec, p.para, s, e, JSON.stringify(props));
        if (p.path.length !== 1) return null;
        const c = p.path[0];
        return doc.applyCharFormatInCell(p.sec, p.para, c.controlIndex, c.cellIndex, c.cellParaIndex, s, e, JSON.stringify(props));
      },
    };
  };
  const after = (p, off) => ({ ...p.pos, charOffset: off });

  /** 스냅샷 하나로 문서를 고친다(되돌리기 한 번) */
  const run = (ih, operationType, fn) => {
    ih.executeOperation({ kind: 'snapshot', operationType, operation: (wasm) => fn(wasm.doc) });
    ih.textarea?.focus();
  };

  /** 간단한 대화상자(rhwp 대화상자와 같은 모양). Enter=넣기, Esc=취소 */
  const dialog = (title, build, onOk) => {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    const wrap = document.createElement('div');
    wrap.className = 'dialog-wrap';
    wrap.style.minWidth = '360px';
    const head = document.createElement('div');
    head.className = 'dialog-title';
    head.textContent = title;
    const close = document.createElement('button');
    close.className = 'dialog-close';
    close.textContent = '×';
    head.appendChild(close);
    const body = document.createElement('div');
    body.className = 'dialog-body';
    body.style.cssText = 'display:flex;flex-direction:column;gap:8px;padding:12px 16px;';
    const foot = document.createElement('div');
    foot.className = 'dialog-footer';
    const ok = document.createElement('button');
    ok.className = 'dialog-btn dialog-btn-primary';
    ok.textContent = '넣기(D)';
    const cancel = document.createElement('button');
    cancel.className = 'dialog-btn';
    cancel.textContent = '취소';
    foot.append(ok, cancel);
    wrap.append(head, body, foot);
    overlay.appendChild(wrap);
    const get = build(body) ?? (() => ({}));
    const hide = () => overlay.remove();
    const submit = () => { const v = get(); if (v === false) return; hide(); onOk(v); };
    close.onclick = hide;
    cancel.onclick = hide;
    ok.onclick = submit;
    overlay.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') { e.stopPropagation(); hide(); getInputHandler()?.textarea?.focus(); }
      if (e.key === 'Enter' && !e.isComposing) { e.preventDefault(); e.stopPropagation(); submit(); }
    });
    document.body.appendChild(overlay);
    setTimeout(() => (body.querySelector('input, select') ?? ok).focus(), 0);
  };
  const row = (body, label, el) => {
    const r = document.createElement('label');
    r.style.cssText = 'display:flex;align-items:center;gap:8px;';
    const s = document.createElement('span');
    s.className = 'dialog-label';
    s.style.minWidth = '110px';
    s.textContent = label;
    r.append(s, el);
    body.appendChild(r);
    return el;
  };
  const input = (value = '') => {
    const i = document.createElement('input');
    i.className = 'dialog-input';
    i.style.flex = '1';
    i.value = value;
    return i;
  };
  const note = (body, text) => {
    const d = document.createElement('div');
    d.style.cssText = 'font-size:12px;opacity:.75;';
    d.textContent = text;
    body.appendChild(d);
  };

  // ── 하이퍼링크 ──────────────────────────────────────────
  const hyperlink = (ih) => {
    const p = place(ih);
    if (!p) return;
    const selText = host.read((doc) => { try { return ops(doc, p).text(p.start, p.end); } catch { return ''; } });
    dialog('하이퍼링크', (body) => {
      const shown = row(body, '표시할 문자열(T):', input(selText));
      const url = row(body, '연결 대상(U):', input(/^(https?:\/\/|www\.)/i.test(selText) ? selText : 'https://'));
      note(body, '웹 주소나 전자 우편 주소를 적는다. 선택한 글이 있으면 그 글이 연결된다.');
      return () => {
        const u = url.value.trim();
        if (!u || u === 'https://') { url.focus(); return false; }
        return { text: shown.value || u, url: /^www\./i.test(u) ? `http://${u}` : u };
      };
    }, ({ text, url }) => {
      const isMail = /^mailto:|^[^/@\s]+@[^/@\s]+$/.test(url);
      const target = isMail && !url.startsWith('mailto:') ? `mailto:${url}` : url;
      const params = '<hp:parameters cnt="6" name="">'
        + '<hp:integerParam name="Prop">0</hp:integerParam>'
        + `<hp:stringParam name="Command">${xml(hwpEsc(target))};1;0;0;</hp:stringParam>`
        + `<hp:stringParam name="Path">${xml(target)}</hp:stringParam>`
        + `<hp:stringParam name="Category">${isMail ? 'HWPHYPERLINK_TYPE_EMAIL' : 'HWPHYPERLINK_TYPE_URL'}</hp:stringParam>`
        + '<hp:stringParam name="TargetType">HWPHYPERLINK_TARGET_BOOKMARK</hp:stringParam>'
        + '<hp:stringParam name="DocOpenType">HWPHYPERLINK_JUMP_CURRENTTAB</hp:stringParam>'
        + '</hp:parameters>';
      run(ih, 'insertHyperlink', (doc) => {
        const o = ops(doc, p);
        o.del(p.start, p.end - p.start);
        const r = o.field(p.start, 'hyperlink', text, params);
        o.charFmt(r.start, r.end, { textColor: '#0000FF', underline: true });
        return after(p, r.end);
      });
    });
  };

  // ── 상호 참조(책갈피가 있는 쪽 번호) ─────────────────────
  const crossRef = (ih) => {
    const p = place(ih);
    if (!p) return;
    const marks = host.read((doc) => { try { return JSON.parse(doc.getBookmarks()); } catch { return []; } });
    dialog('상호 참조', (body) => {
      if (!marks.length) {
        note(body, '문서에 책갈피가 없다. 먼저 Ctrl+K,B 로 책갈피를 넣는다.');
        return () => false;
      }
      const sel = document.createElement('select');
      sel.className = 'dialog-select';
      sel.style.flex = '1';
      for (const m of marks) {
        const o = document.createElement('option');
        o.value = m.name;
        o.textContent = m.name;
        sel.appendChild(o);
      }
      row(body, '참조할 책갈피(B):', sel);
      note(body, '참조 내용: 쪽 번호(책갈피가 있는 쪽)');
      return () => marks.find((m) => m.name === sel.value);
    }, (mark) => {
      const page = host.read((doc) => {
        try {
          const sec = mark.sec ?? mark.section ?? mark.sectionIndex ?? 0;
          const para = mark.para ?? mark.paragraph ?? mark.paraIdx ?? 0;
          return JSON.parse(doc.getCursorRect(sec, para, mark.charPos ?? 0)).pageIndex + 1;
        } catch { return 1; }
      });
      const params = '<hp:parameters cnt="8" name="">'
        + '<hp:booleanParam name="Fiexde">1</hp:booleanParam>'
        + '<hp:integerParam name="Prop">0</hp:integerParam>'
        + `<hp:stringParam name="Command">?${xml(hwpEsc(mark.name))};6;0;0;0;</hp:stringParam>`
        + `<hp:stringParam name="RefPath">?${xml(hwpEsc(mark.name))};</hp:stringParam>`
        + '<hp:stringParam name="RefType">TARGET_BOOKMARK</hp:stringParam>'
        + '<hp:stringParam name="RefContentType">OBJECT_TYPE_PAGE</hp:stringParam>'
        + '<hp:booleanParam name="RefHyperLink">false</hp:booleanParam>'
        + '<hp:stringParam name="RefOpenType">HWPHYPERLINK_JUMP_CURRENTTAB</hp:stringParam>'
        + '</hp:parameters>';
      run(ih, 'insertCrossRef', (doc) => {
        const r = ops(doc, p).field(p.end, 'crossref', String(page), params);
        return after(p, r.end);
      });
    });
  };

  // ── 날짜/시간 ──────────────────────────────────────────
  const insertString = (ih, key) => {
    const p = place(ih);
    if (!p) return;
    const t = formatDate(new Date(), key);
    run(ih, 'insertDateString', (doc) => {
      const o = ops(doc, p);
      o.del(p.start, p.end - p.start);
      o.ins(p.start, t);
      return after(p, p.start + t.length);
    });
  };
  const dateCode = (ih) => {
    const p = place(ih);
    if (!p) return;
    // 한/글의 「날짜/시간 코드」는 문서 요약의 만든 날짜 필드다(type="SUMMERY", Command $createtime)
    const params = '<hp:parameters cnt="3" name="">'
      + '<hp:integerParam name="Prop">8</hp:integerParam>'
      + '<hp:stringParam name="Command">$createtime</hp:stringParam>'
      + '<hp:stringParam name="Property">$createtime</hp:stringParam>'
      + '</hp:parameters>';
    run(ih, 'insertDateCode', (doc) => {
      const r = ops(doc, p).field(p.end, 'summary', formatDate(new Date(), 'full'), params);
      return after(p, r.end);
    });
  };
  const dateFormat = (ih) => {
    dialog('날짜/시간 형식', (body) => {
      const cur = savedFormat();
      const now = new Date();
      const radios = FORMATS.map(([key], i) => {
        const r = document.createElement('input');
        r.type = 'radio';
        r.name = 'hwpx-date-fmt';
        r.value = key;
        r.checked = key === cur;
        const l = document.createElement('label');
        l.style.cssText = 'display:flex;gap:8px;align-items:center;';
        l.append(r, document.createTextNode(`${formatDate(now, key)}(${i + 1})`));
        body.appendChild(l);
        return r;
      });
      note(body, '고른 형식은 Ctrl+K,D 의 기본 형식으로도 기억한다.');
      return () => ({ key: radios.find((r) => r.checked)?.value ?? 'ymd' });
    }, ({ key }) => {
      try { localStorage.setItem(FMT_KEY, key); } catch { /* 기억 못 해도 넣기는 한다 */ }
      insertString(ih, key);
    });
  };

  const COMMANDS = [
    ['insert:hyperlink', '하이퍼링크', hyperlink],
    ['insert:cross-ref', '상호 참조', crossRef],
    ['insert:date-string', '날짜/시간 문자열', (ih) => insertString(ih, savedFormat())],
    ['insert:date-code', '날짜/시간 코드', dateCode],
    ['insert:date-format', '날짜/시간 형식', dateFormat],
  ];
  const patch = () => {
    const ih = getInputHandler();
    const reg = ih?.dispatcher?.registry;
    if (!reg) return false;
    if (reg.get('insert:hyperlink')?.__k) return true;
    for (const [id, label, fn] of COMMANDS) {
      reg.register({ id, label, canExecute: (ctx) => ctx.hasDocument, execute: (services) => fn(services.getInputHandler()), __k: true });
    }
    return true;
  };
  if (!patch()) {
    const t = setInterval(() => { if (patch()) clearInterval(t); }, 200);
  }
}
