// @ts-nocheck
/**
 * 그림 오른쪽 클릭 메뉴의 「그림 자르기」(2026-09-27 사용자 요청). 누르면 그림 위에 자르기 틀이 뜨고, 네 변과 네 모서리
 * 손잡이를 안으로 끌면 잘리고 밖으로 끌면 잘랐던 부분이 되살아난다(한/글 방식). Enter, 두 번 누르기, 틀 바깥 누르기는
 * 적용, Esc 는 취소. 적용은 되돌리기 한 번으로 돌아간다.
 *
 * 값 계산: rhwp 속성 API 의 cropLeft..Bottom 은 네 방향에서 잘라 낸 양(원본 그림 기준 HWPUNIT)이다.
 * 화면 배율 s = 개체 폭 / (원본 폭 - 왼쪽 - 오른쪽). 변을 d(HWPUNIT)만큼 안으로 끌면 자른 양 += d / s, 개체 폭 -= d.
 * 왼쪽, 위쪽을 끌면 글자처럼 취급하지 않는 그림은 위치도 d 만큼 옮긴다.
 * 머리말/꼬리말, 각주 안 그림은 속성 대화상자의 그림 탭으로 연다.
 */
const ID = 'claude:picture-crop';
const HU_PER_PX = 75;
const MIN_PX = 8;
const DIRS = ['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w'];
const CURSOR = { nw: 'nwse-resize', se: 'nwse-resize', ne: 'nesw-resize', sw: 'nesw-resize', n: 'ns-resize', s: 'ns-resize', e: 'ew-resize', w: 'ew-resize' };

function focusCropFields() {
  const ov = [...document.querySelectorAll('.modal-overlay')].pop();
  if (!ov) return false;
  const tab = [...ov.querySelectorAll('.dialog-tab')].find((b) => b.textContent.trim() === '그림');
  if (!tab) return false;
  tab.click();
  const fs = [...ov.querySelectorAll('fieldset')].find((f) => f.querySelector('legend')?.textContent.includes('그림 자르기'));
  const input = fs?.querySelector('input');
  if (!input) return false;
  input.focus();
  input.select?.();
  return true;
}

function openDialogFallback(ih) {
  ih.dispatcher.dispatch('insert:picture-props');
  let tries = 0;
  const t = setInterval(() => { if (focusCropFields() || ++tries > 20) clearInterval(t); }, 50);
}

/** 선택한 그림의 속성 읽기/쓰기 함수(본문 그림, 셀 안 그림). 그 밖은 null. */
function propsAccess(ih, ref) {
  const w = ih.wasm;
  if (ref.headerFooter || ref.noteRef) return null;
  const cellPath = ref.cellPath ?? (ref.cellIdx !== undefined && ref.cellParaIdx !== undefined && ref.outerTableControlIdx !== undefined
    ? [{ controlIndex: ref.outerTableControlIdx, cellIndex: ref.cellIdx, cellParaIndex: ref.cellParaIdx }] : null);
  if (cellPath) {
    return {
      get: () => w.getCellPicturePropertiesByPath(ref.sec, ref.ppi, cellPath, ref.ci),
      set: (bridge, props) => bridge.setCellPicturePropertiesByPath(ref.sec, ref.ppi, cellPath, ref.ci, props),
    };
  }
  return {
    get: () => w.getPictureProperties(ref.sec, ref.ppi, ref.ci),
    set: (bridge, props) => bridge.setPictureProperties(ref.sec, ref.ppi, ref.ci, props),
  };
}

let active = null;   // 진행 중인 자르기(한 번에 하나)

function startCrop(ih) {
  const ref = ih.getSelectedPictureRef?.();
  if (!ref || ref.type !== 'image') return;
  const acc = propsAccess(ih, ref);
  const bbox = ih.findPictureBbox?.(ref);
  const renderer = ih.pictureObjectRenderer;
  const content = document.querySelector('#scroll-content');
  if (!acc || !bbox || !renderer?.virtualScroll || !content) { openDialogFallback(ih); return; }
  let p;
  try { p = acc.get(); } catch { openDialogFallback(ih); return; }
  if (p.sizeProtect) return;   // 크기 고정 그림은 자르지 않는다

  const zoom = ih.viewportManager.getZoom();
  const vs = renderer.virtualScroll;
  // 여러 쪽 보기면 쪽이 가운데가 아니다 — 쪽 배치 좌표를 쓴다
  const left = vs.getPageLeftResolved(bbox.pageIndex, content.clientWidth) + bbox.x * zoom;
  const top = vs.getPageOffset(bbox.pageIndex) + bbox.y * zoom;
  const W = bbox.w * zoom;
  const H = bbox.h * zoom;
  // 화면 1px 이 원본 그림에서 차지하는 HWPUNIT
  const sx = p.width / Math.max(1, p.originalWidth - p.cropLeft - p.cropRight);
  const sy = p.height / Math.max(1, p.originalHeight - p.cropTop - p.cropBottom);
  const pxToHu = HU_PER_PX / zoom;
  // 밖으로 되살릴 수 있는 한도(화면 px)
  const ext = {
    l: (p.cropLeft * sx) / pxToHu, r: (p.cropRight * sx) / pxToHu,
    t: (p.cropTop * sy) / pxToHu, b: (p.cropBottom * sy) / pxToHu,
  };

  renderer.clear();
  const root = document.createElement('div');
  root.className = 'claude-crop';
  root.style.cssText = `position:absolute;left:${left}px;top:${top}px;width:${W}px;height:${H}px;z-index:9;pointer-events:auto;`;
  const clip = document.createElement('div');   // 어둡게 칠할 범위 = 되살릴 수 있는 최대 범위
  clip.style.cssText = `position:absolute;left:${-ext.l}px;top:${-ext.t}px;width:${W + ext.l + ext.r}px;height:${H + ext.t + ext.b}px;overflow:hidden;pointer-events:none;`;
  const keepEl = document.createElement('div');
  clip.appendChild(keepEl);
  root.appendChild(clip);
  const k = { l: 0, t: 0, r: W, b: H };   // 남길 영역(root 기준 px)
  const handles = {};
  for (const d of DIRS) {
    const h = document.createElement('div');
    h.dataset.dir = d;
    h.style.cssText = `position:absolute;width:12px;height:12px;background:#000;border:1px solid #fff;box-sizing:border-box;cursor:${CURSOR[d]};`;
    root.appendChild(h);
    handles[d] = h;
  }
  const draw = () => {
    keepEl.style.cssText = `position:absolute;left:${k.l + ext.l}px;top:${k.t + ext.t}px;width:${k.r - k.l}px;height:${k.b - k.t}px;` +
      'outline:1px dashed #000;box-shadow:0 0 0 4000px rgba(0,0,0,.4);';
    const cx = (k.l + k.r) / 2, cy = (k.t + k.b) / 2;
    const pos = { nw: [k.l, k.t], n: [cx, k.t], ne: [k.r, k.t], e: [k.r, cy], se: [k.r, k.b], s: [cx, k.b], sw: [k.l, k.b], w: [k.l, cy] };
    for (const d of DIRS) { handles[d].style.left = `${pos[d][0] - 6}px`; handles[d].style.top = `${pos[d][1] - 6}px`; }
  };
  draw();
  content.appendChild(root);

  let drag = null;
  root.addEventListener('pointerdown', (e) => {
    e.stopPropagation();
    e.preventDefault();
    const dir = e.target?.dataset?.dir;
    if (!dir) return;
    drag = { dir, x: e.clientX, y: e.clientY, start: { ...k } };
    e.target.setPointerCapture?.(e.pointerId);
  });
  root.addEventListener('pointermove', (e) => {
    if (!drag) return;
    const dx = e.clientX - drag.x, dy = e.clientY - drag.y, s = drag.start;
    if (drag.dir.includes('w')) k.l = Math.min(Math.max(s.l + dx, -ext.l), k.r - MIN_PX);
    if (drag.dir.includes('e')) k.r = Math.max(Math.min(s.r + dx, W + ext.r), k.l + MIN_PX);
    if (drag.dir.includes('n')) k.t = Math.min(Math.max(s.t + dy, -ext.t), k.b - MIN_PX);
    if (drag.dir.includes('s')) k.b = Math.max(Math.min(s.b + dy, H + ext.b), k.t + MIN_PX);
    draw();
  });
  root.addEventListener('pointerup', (e) => { drag = null; e.stopPropagation(); });
  for (const t of ['mousedown', 'mouseup', 'click', 'contextmenu']) root.addEventListener(t, (e) => e.stopPropagation());
  root.addEventListener('dblclick', (e) => { e.stopPropagation(); finish(true); });

  const onKey = (e) => {
    if (e.key === 'Escape') { e.preventDefault(); e.stopImmediatePropagation(); finish(false); }
    else if (e.key === 'Enter') { e.preventDefault(); e.stopImmediatePropagation(); finish(true); }
  };
  const onOutside = (e) => { if (!root.contains(e.target)) finish(true); };
  window.addEventListener('keydown', onKey, true);
  setTimeout(() => document.addEventListener('mousedown', onOutside, true), 0);

  function finish(apply) {
    if (!active) return;
    active = null;
    window.removeEventListener('keydown', onKey, true);
    document.removeEventListener('mousedown', onOutside, true);
    root.remove();
    const dl = k.l * pxToHu, dr = (W - k.r) * pxToHu, dt = k.t * pxToHu, db = (H - k.b) * pxToHu;
    if (apply && [dl, dr, dt, db].some((v) => Math.abs(v) >= 1)) {
      const props = {
        width: Math.round(p.width - dl - dr),
        height: Math.round(p.height - dt - db),
        cropLeft: Math.max(0, Math.round(p.cropLeft + dl / sx)),
        cropRight: Math.max(0, Math.round(p.cropRight + dr / sx)),
        cropTop: Math.max(0, Math.round(p.cropTop + dt / sy)),
        cropBottom: Math.max(0, Math.round(p.cropBottom + db / sy)),
      };
      if (!p.treatAsChar) {
        props.horzOffset = Math.round(p.horzOffset + dl);
        props.vertOffset = Math.round(p.vertOffset + dt);
      }
      try {
        ih.executeOperation({
          kind: 'snapshot',
          operationType: 'cropPicture',
          operation: (bridge) => { acc.set(bridge, props); return ih.getCursorPosition(); },
        });
      } catch (err) {
        console.warn('[claude] 그림 자르기 실패:', err);
      }
    }
    try { ih.renderPictureObjectSelection?.(); } catch { /* 선택이 풀렸으면 무시 */ }
  }
  active = { finish };
}

/**
 * 그림 위에서 바로 오른쪽 클릭해도 그림 메뉴가 뜨게 한다(2026-09-27 사용자 요청). rhwp 는 그림이 이미 선택돼 있을 때만
 * 그림 메뉴를 보여 준다. 스튜디오보다 먼저 contextmenu 를 받아, 누른 자리에 그림이 있으면 그 자리에 왼쪽 클릭을 보내
 * 스튜디오 방식대로 그림을 고른 뒤 원래 처리로 넘긴다. 그림이 없는 자리(글자)는 건드리지 않아 캐럿과 선택이 그대로다.
 */
function installRightClickSelect(getInputHandler) {
  document.addEventListener('contextmenu', (e) => {
    const ih = getInputHandler();
    if (!ih || ih.cursor?.isInPictureObjectSelection?.()) return;
    const content = document.querySelector('#scroll-content');
    if (!content || !content.contains(e.target)) return;
    try {
      const zoom = ih.viewportManager.getZoom();
      const r = content.getBoundingClientRect();
      const cx = e.clientX - r.left, cy = e.clientY - r.top;
      const vs = ih.virtualScroll;
      const pi = vs.getPageAtPoint(cx, cy);
      const px = (cx - vs.getPageLeftResolved(pi, content.clientWidth)) / zoom;
      const py = (cy - vs.getPageOffset(pi)) / zoom;
      if (!ih.findPictureAtClick(pi, px, py)) return;
    } catch { return; }
    const init = { bubbles: true, cancelable: true, clientX: e.clientX, clientY: e.clientY, button: 0, buttons: 1, view: window };
    e.target.dispatchEvent(new MouseEvent('mousedown', init));
    e.target.dispatchEvent(new MouseEvent('mouseup', { ...init, buttons: 0 }));
  }, true);
}

export function installPictureCrop(getInputHandler) {
  installRightClickSelect(getInputHandler);
  const patch = () => {
    const ih = getInputHandler();
    const reg = ih?.dispatcher?.registry;
    if (!reg || !reg.get('insert:picture-props')) return false;
    if (reg.get(ID)) return true;
    reg.register({
      id: ID,
      label: '그림 자르기',
      canExecute: (ctx) => ctx.inPictureObjectSelection,
      execute: (services) => {
        const h = services.getInputHandler();
        if (!h || active) return;
        // 오른쪽 클릭 메뉴가 닫힌 뒤에 틀을 띄운다(메뉴 닫기의 mousedown 이 바로 적용하지 않게)
        setTimeout(() => startCrop(h), 0);
      },
    });
    const proto = Object.getPrototypeOf(ih);
    if (!proto.__pictureCrop) {
      proto.__pictureCrop = true;
      const orig = proto.getPictureObjectContextMenuItems;
      proto.getPictureObjectContextMenuItems = function () {
        const items = orig.call(this);
        if (this.getSelectedPictureRef?.()?.type !== 'image') return items;
        const at = items.findIndex((x) => x.commandId === 'insert:picture-props');
        items.splice(at < 0 ? items.length : at, 0, { type: 'command', commandId: ID, label: '그림 자르기' });
        return items;
      };
    }
    return true;
  };
  if (!patch()) {
    const t = setInterval(() => { if (patch()) clearInterval(t); }, 200);
  }
}
