/**
 * [claude-hwpx move-drop-line] 표, 그림 끌어 옮기기: 끄는 동안은 놓일 자리(문단 사이)만 푸른 가로선으로 보여 주고,
 * 마우스를 놓으면 엔진 moveControlToParagraph 로 개체를 그 자리로 옮긴다(되돌리기 한 번).
 * 종전에는 끄는 동안 오프셋을 계속 바꿔 문서가 흔들렸고, 옮긴 뒤 원래 문단 자리가 비어 여백이 생겼다(2026-09-28 사용자 요청).
 */

export interface DropTarget {
  sec: number;
  /** 옮겨 갈 문단 자리(그 문단 앞. 문단 수면 맨 끝) */
  dst: number;
}

const LINE_ID = 'claude-move-drop-line';

function lineEl(ih: any): HTMLDivElement | null {
  const sc = ih.container.querySelector('#scroll-content') as HTMLElement | null;
  if (!sc) return null;
  let el = sc.querySelector(`#${LINE_ID}`) as HTMLDivElement | null;
  if (!el) {
    el = document.createElement('div');
    el.id = LINE_ID;
    el.style.cssText = 'position:absolute;height:2px;background:#1e6fff;pointer-events:none;z-index:30;display:none;';
    sc.appendChild(el);
  }
  return el;
}

export function clearDropLine(ih: any): void {
  const el = lineEl(ih);
  if (el) el.style.display = 'none';
}

/** 문단 p 의 쪽 기준 윗변, 아랫변(px)과 쪽 번호. 캐럿 좌표로 구한다 */
function paraBand(ih: any, sec: number, p: number): { page: number; top: number; bottom: number } | null {
  try {
    const first = ih.wasm.getCursorRect(sec, p, 0);
    const len = ih.wasm.getParagraphLength(sec, p);
    const last = len > 0 ? ih.wasm.getCursorRect(sec, p, len) : first;
    if (!first) return null;
    const bottom = last && last.pageIndex === first.pageIndex ? last.y + last.height : first.y + first.height;
    return { page: first.pageIndex, top: first.y, bottom };
  } catch {
    // 표만 담은 문단은 캐럿 좌표가 없을 수 있다 — 표 상자로 잰다
    try {
      const b = ih.wasm.getTableBBox(sec, p, 0);
      return { page: b.pageIndex, top: b.y, bottom: b.y + b.height };
    } catch {
      return null;
    }
  }
}

/**
 * 마우스 위치에서 놓일 자리를 정하고 푸른 선을 그린다. 자기 자리(옮겨도 그대로)면 선을 숨기고 null.
 * srcPpi: 옮기는 개체를 담은 본문 문단. sole: 그 문단이 개체만 담았는가(자기 앞, 뒤 자리는 제자리다)
 */
export function updateDropLine(ih: any, e: MouseEvent, srcSec: number, srcPpi: number, sole: boolean): DropTarget | null {
  const zoom = ih.viewportManager.getZoom();
  const sc = ih.container.querySelector('#scroll-content') as HTMLElement | null;
  if (!sc) return null;
  const cr = sc.getBoundingClientRect();
  const cx = e.clientX - cr.left;
  const cy = e.clientY - cr.top;
  const pi = ih.virtualScroll.getPageAtPoint(cx, cy);
  const po = ih.virtualScroll.getPageOffset(pi);
  const pl = ih.virtualScroll.getPageLeftResolved(pi, sc.clientWidth);
  const px = (cx - pl) / zoom;
  const py = (cy - po) / zoom;
  let hit: any;
  try {
    hit = ih.wasm.hitTest(pi, px, py);
  } catch {
    clearDropLine(ih);
    return null;
  }
  if (!hit || hit.sectionIndex !== srcSec || hit.isTextBox) {
    clearDropLine(ih);
    return null;
  }
  const sec = hit.sectionIndex;
  const p = hit.parentParaIndex ?? hit.paragraphIndex;
  const band = paraBand(ih, sec, p);
  if (!band) {
    clearDropLine(ih);
    return null;
  }
  const bandPage = band.page;
  const pointerY = bandPage === pi ? py : band.top;
  const after = pointerY > (band.top + band.bottom) / 2;
  const dst = after ? p + 1 : p;
  if (dst === srcPpi || (sole && dst === srcPpi + 1)) {
    clearDropLine(ih);
    return null;
  }
  // 선: 그 문단 윗변(앞에 놓을 때) 또는 아랫변(뒤에 놓을 때), 본문 폭
  const el = lineEl(ih);
  if (el) {
    let info: any = null;
    try { info = ih.wasm.getPageInfo(bandPage); } catch { /* 쪽 정보 없음 */ }
    const left = ih.virtualScroll.getPageLeftResolved(bandPage, sc.clientWidth);
    const top = ih.virtualScroll.getPageOffset(bandPage);
    const x0 = info ? info.marginLeft : 40;
    const w = info ? info.width - info.marginLeft - info.marginRight : 600;
    const y = after ? band.bottom : band.top;
    el.style.left = `${left + x0 * zoom}px`;
    el.style.top = `${top + y * zoom - 1}px`;
    el.style.width = `${w * zoom}px`;
    el.style.display = 'block';
  }
  return { sec, dst };
}

/** 옮기기 실행(되돌리기 한 번). 새 문단, 컨트롤 번호를 돌려준다 */
export function applyDrop(ih: any, sec: number, ppi: number, ci: number, dst: number): { ppi: number; ci: number } | null {
  let out: { ppi: number; ci: number } | null = null;
  try {
    ih.executeOperation({
      kind: 'snapshot',
      operationType: 'moveControlToParagraph',
      operation: (w: any) => {
        const doc = w.doc ?? w;
        const r = JSON.parse(doc.moveControlToParagraph(sec, ppi, ci, dst));
        if (r?.ok) out = { ppi: r.ppi, ci: r.ci };
        return { sectionIndex: sec, paragraphIndex: out?.ppi ?? ppi, charOffset: 0 };
      },
    });
  } catch (err) {
    console.warn('[claude move-drop] 옮기기 실패:', err);
    return null;
  }
  return out;
}

/** 본문 문단 ppi 가 개체 ci 하나만 담았는가 */
export function isSoleControlPara(ih: any, sec: number, ppi: number): boolean {
  try {
    return ih.wasm.getParagraphLength(sec, ppi) <= 1;
  } catch {
    return false;
  }
}
