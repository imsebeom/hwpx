// @ts-nocheck
/**
 * 한컴 한/글 기본 단축키 층. claude 플러그인이 studio 창에 설치한다(캡처 단계라 studio 보다 먼저 받는다).
 *
 * 근거: 한/글 2020·2022·2024 도움말 「단축키 일람」(help.hancom.com/hoffice130/ko-KR/Hwp/view/toolbar/shortcut(table).htm).
 * rhwp 는 브라우저 예약키를 피하려고 일부 한컴 키를 옮겨 두었다(Ctrl+N 계열 → Ctrl+M, Ctrl+Shift+C/R/T → Alt+Shift+C/H/D).
 * 여기서는 한컴 원래 키를 되살리고, rhwp 가 옮겨 둔 키는 건드리지 않는다(브라우저에서도 계속 쓸 수 있게).
 * Ctrl+N 은 크롬 일반 탭에서는 페이지에 오지 않는다 — 에디터 앱 창(WebView2, app.py)에서 쓴다.
 *
 * 두 번째 키는 e.code(물리 키)로 판별한다. 한글 입력기가 켜져 있으면 e.key 가 'Process' 나 'ㅜ' 로 오기 때문이다.
 */
import { matchShortcut, defaultShortcuts } from '@/command/shortcut-map';

/**
 * 글쇠 판별: 물리 키(e.code)를 먼저 본다. 원격 데스크톱이나 매크로 입력처럼 code 가 비어 오면
 * 가상 키 코드(keyCode 65~90)로 대신한다. 입력기 조합 중에는 keyCode 가 229 라 code 만 믿을 수 있다.
 */
const LETTER = (e) => {
  if (/^Key[A-Z]$/.test(e.code)) return e.code.slice(3).toLowerCase();
  if (!e.code && e.keyCode >= 65 && e.keyCode <= 90) return String.fromCharCode(e.keyCode).toLowerCase();
  return null;
};
/** e.code 가 비어 있으면 가상 키 코드에서 같은 이름(KeyA, Insert …)을 만든다. */
const CODE = (e) => {
  if (e.code) return e.code;
  const k = LETTER(e);
  if (k) return `Key${k.toUpperCase()}`;
  return { 45: 'Insert', 46: 'Delete', 121: 'F10' }[e.keyCode] ?? '';
};

// Ctrl+N,? (넣기). 값이 함수면 문맥에 따라 고른다. 없는 기능은 null(아무것도 안 하고 키를 삼킨다).
const CHORD_N = {
  t: 'table:create',
  i: 'insert:image',
  n: 'insert:footnote',
  e: 'insert:endnote',
  m: 'insert:equation',
  b: 'insert:textbox',
  c: (ctx) => (ctx.inTable ? 'table:caption-toggle' : 'insert:caption-toggle'),
  h: 'page:header-create',
  s: 'page:hide',
  g: 'page:section-settings',
  k: 'format:object-properties',
  a: 'table:split',
  z: 'table:attach',
  f: 'table:formula',
  p: null, // 쪽 번호 매기기(pageNum 컨트롤) — rhwp 에 없다. 머리말/꼬리말 쪽 번호는 Claude 에게 요청
  l: null, // 문단 띠
  o: null, // OLE 개체
  d: null, // 호환 문서
};

// Ctrl+Q,? (찾기)
const CHORD_Q = {
  f: 'edit:find',
  a: 'edit:find-replace',
};

// Ctrl+M,? — 한컴에서는 글자 색. 색이 아닌 글쇠는 rhwp 가 옮겨 둔 Ctrl+N 계열 그대로 둔다.
const COLORS = {
  k: '#000000', r: '#FF0000', b: '#0000FF', d: '#993366', g: '#008000', y: '#FFFF00', c: '#008080', w: '#FFFFFF',
};
const CHORD_M_FALLBACK = { a: 'table:split', z: 'table:attach', n: 'insert:footnote', s: 'page:hide', m: 'insert:equation', f: 'table:formula' };

// 한 번에 누르는 키: [ctrl, shift, alt, code] → 명령
const SINGLE = [
  [true, true, false, 'KeyC', 'format:align-center'],
  [true, true, false, 'KeyR', 'format:align-right'],
  [true, true, false, 'KeyT', 'format:align-distribute'],
  [true, false, false, 'KeyH', 'edit:find-replace'],
  [true, false, false, 'KeyJ', 'page:break'],
  [true, false, false, 'F10', 'insert:symbols'],
  [true, true, false, 'Insert', 'format:toggle-numbering'],
  [true, true, false, 'Delete', 'format:toggle-bullet'],
  [false, true, true, 'KeyP', 'format:superscript'],
  [false, true, true, 'KeyS', 'format:subscript'],
  [false, false, true, 'Insert', 'table:insert-row-col'],
];

// 셀 블록(F5, 여러 셀 선택)을 유지한 채 부를 명령. rhwp 는 셀 선택 중에 온 키를 「그 외 키」로 보고
// 셀 선택을 먼저 풀어 버려(input-handler-keyboard.ts) Alt+Shift+A/Z, Alt+L 같은 서식이 커서 셀 하나에만
// 들어갔다. 서식 명령과 대화상자(글자 모양, 문단 모양, 스타일)는 getSelectedCellBlock 으로 블록 전체를
// 대상으로 삼으므로 선택을 풀기 전에 부른다. 블록 계산과 줄·칸 추가/삭제도 블록이 있어야 뜻이 선다.
const keepsCellBlock = (id) =>
  id.startsWith('format:') ||
  ['table:block-avg', 'table:block-product', 'table:insert-row-col', 'table:delete-row-col'].includes(id);

export function installHancomKeys(host, getInputHandler) {
  let pending = null;       // 'N' | 'Q' | 'M'
  let pendingTimer = null;

  // rhwp 자신의 단축키(Ctrl+M 계열 등)와 같은 경로로 명령을 부른다. 플러그인용 host.automation 은
  // 대화상자를 여는 명령(표 만들기, 찾아 바꾸기 …)을 allowDialog 를 줘도 열지 않았다(2026-09-25 앱 창 실측).
  const runCommand = (id) => {
    const d = getInputHandler()?.dispatcher;
    if (d) d.dispatch(id);
    else Promise.resolve(host.automation.execute(id, {}, { allowDialog: true })).catch(() => {});
  };
  const ctx = () => {
    try { return host.automation.getContext(); } catch { return {}; }
  };
  const swallow = (e) => { e.preventDefault(); e.stopImmediatePropagation(); };
  const arm = (which) => {
    pending = which;
    clearTimeout(pendingTimer);
    pendingTimer = setTimeout(() => { pending = null; }, 2000);
  };

  /** 셀 안이면 그 셀의 글 전체를 고른다(한/글 모두 선택). 처리했으면 true. */
  const selectCellContents = () => {
    const ih = getInputHandler();
    if (!ih) return false;
    const pos = ih.getCursorPosition?.();
    if (!pos || pos.parentParaIndex == null) return false;
    if ((pos.cellPath?.length ?? 1) > 1) return false; // 셀 안 표의 셀은 rhwp 기본 동작에 맡긴다
    const range = host.read((doc) => {
      const n = doc.getCellParagraphCount(pos.sectionIndex, pos.parentParaIndex, pos.controlIndex, pos.cellIndex);
      const last = Math.max(0, n - 1);
      return { last, len: doc.getCellParagraphLength(pos.sectionIndex, pos.parentParaIndex, pos.controlIndex, pos.cellIndex, last) };
    });
    ih.cursor.clearSelection();
    ih.cursor.moveTo({ ...pos, cellParaIndex: 0, charOffset: 0 });
    ih.cursor.setAnchor();
    ih.cursor.moveTo({ ...pos, cellParaIndex: range.last, charOffset: range.len });
    ih.cursor.resetPreferredX?.();
    ih.updateCaret?.(true);
    return true;
  };

  const onKey = (e) => {
    // 에디터 본문 입력칸(rhwp 의 숨은 textarea)에서 온 키만 받는다. 대화상자 입력칸의 Ctrl+A 등은 건드리지 않는다.
    const ih = getInputHandler();
    if (!ih || !ih.active || e.target !== ih.textarea) return;
    if (e.repeat && pending) return;
    const ctrl = e.ctrlKey || e.metaKey;

    // 두 번째 키
    const code = CODE(e);
    if (pending && !['Control', 'Shift', 'Alt', 'Meta'].includes(e.key)) {
      const which = pending;
      pending = null;
      clearTimeout(pendingTimer);
      const k = LETTER(e);
      if (!k) return; // 글쇠가 아니면 평소대로
      swallow(e);
      // 한글 입력기가 이 키를 잡으면 preventDefault 로도 조합이 멈추지 않는다. 조합은 다음 키까지 열려 있다가
      // 「ㄱ」 같은 글자로 확정되고, 선택 영역이 있으면 그것을 덮어쓴다(2026-09-25 앱 창 실측).
      // 입력칸 포커스를 뺐다 돌려 조합을 바로 끝내고, 그 사이의 조합·입력 이벤트는 rhwp 에 넘기지 않는다.
      if (e.isComposing || e.keyCode === 229 || e.key === 'Process' || /^[ㄱ-ㅣ]$/.test(e.key)) dropComposition();
      if (which === 'N') {
        const v = CHORD_N[k];
        const id = typeof v === 'function' ? v(ctx()) : v;
        if (id) runCommand(id);
      } else if (which === 'Q') {
        if (CHORD_Q[k]) runCommand(CHORD_Q[k]);
      } else if (which === 'M') {
        if (COLORS[k]) getInputHandler()?.applyCharFormat?.({ textColor: COLORS[k] });
        else if (CHORD_M_FALLBACK[k]) runCommand(CHORD_M_FALLBACK[k]);
      }
      return;
    }

    // 첫 번째 키 (Ctrl+N / Ctrl+Q / Ctrl+M)
    if (ctrl && !e.shiftKey && !e.altKey) {
      if (code === 'KeyN') { swallow(e); arm('N'); return; }
      if (code === 'KeyQ') { swallow(e); arm('Q'); return; }
      if (code === 'KeyM') { swallow(e); arm('M'); return; }
      if (code === 'KeyA' && selectCellContents()) { swallow(e); return; }
    }

    if (ih.cursor?.isInCellSelectionMode?.() && !ih.cursor.isProtectedCellSelectionMode?.()) {
      const id = matchShortcut(e, defaultShortcuts);
      if (id && keepsCellBlock(id)) {
        swallow(e);
        runCommand(id);
        return;
      }
    }

    for (const [c, s, a, k2, id] of SINGLE) {
      if (ctrl === c && e.shiftKey === s && e.altKey === a && code === k2) {
        swallow(e);
        runCommand(id);
        return;
      }
    }
  };

  // 단축키 글쇠가 연 입력기 조합을 버린다.
  let dropping = false;
  const IME_EVENTS = ['compositionstart', 'compositionupdate', 'compositionend', 'beforeinput', 'input'];
  const onIme = (e) => {
    if (!dropping || e.target !== getInputHandler()?.textarea) return;
    if (e.type === 'beforeinput' && e.cancelable) e.preventDefault();
    e.stopImmediatePropagation();
  };
  function dropComposition() {
    const ta = getInputHandler()?.textarea;
    if (!ta) return;
    dropping = true;
    setTimeout(() => {
      ta.blur();          // 포커스가 빠지면 입력기가 조합을 끝낸다(확정 이벤트도 위에서 버린다)
      ta.focus();
      setTimeout(() => { ta.value = ''; dropping = false; }, 60);
    }, 0);
  }

  window.addEventListener('keydown', onKey, true);
  for (const t of IME_EVENTS) window.addEventListener(t, onIme, true);
  return () => {
    window.removeEventListener('keydown', onKey, true);
    for (const t of IME_EVENTS) window.removeEventListener(t, onIme, true);
  };
}
