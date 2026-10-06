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

// ── 표 속 표 끌어 옮기기(2026-10-07 사용자 보고 「표 속에 표를 드래그 이동시켰는데 상위 표까지 같이 이동되네」) ──
// 끌기가 바깥 표 번호만 써서 바깥 표가 옮겨졌다. 표 속 표는 같은 칸 안의 문단 사이로만 옮긴다(엔진 moveControlInCellByPath).

type PathEntry = { controlIndex: number; cellIndex: number; cellParaIndex: number };

export interface CellDropTarget {
  /** 옮겨 갈 칸 문단 자리(그 문단 앞. 문단 수면 맨 끝) */
  dst: number;
}

/** 표 속 표 경로(칸 경로 + 안쪽 표)에서 그 표를 담은 칸 경로 */
function hostCellPath(tablePath: PathEntry[]): PathEntry[] {
  return tablePath.slice(0, -1).map((x) => ({ ...x }));
}

function withPara(path: PathEntry[], para: number): PathEntry[] {
  const p = path.map((x) => ({ ...x }));
  p[p.length - 1].cellParaIndex = para;
  return p;
}

/** 마우스 위치에서 같은 칸 안의 놓일 자리를 정하고 칸 폭의 푸른 선을 그린다. 다른 칸이나 제자리면 null */
export function updateCellDropLine(ih: any, e: MouseEvent, sel: { sec: number; ppi: number; cellPath: PathEntry[] }): CellDropTarget | null {
  const host = hostCellPath(sel.cellPath);
  const hostPara = host[host.length - 1].cellParaIndex;
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
  try { hit = ih.wasm.hitTest(pi, px, py); } catch { clearDropLine(ih); return null; }
  const hp: PathEntry[] | undefined = hit?.cellPath;
  const sameCell = hit && hit.sectionIndex === sel.sec && hit.parentParaIndex === sel.ppi && !hit.isTextBox
    && Array.isArray(hp) && hp.length >= host.length
    && host.every((h, i) => hp[i].controlIndex === h.controlIndex && hp[i].cellIndex === h.cellIndex);
  if (!sameCell) { clearDropLine(ih); return null; }
  const p = hp![host.length - 1].cellParaIndex;
  // 그 칸 문단의 윗변, 아랫변(쪽 좌표). 개체만 담은 문단은 캐럿 좌표가 없을 수 있어 그때는 놓지 않는다
  let band: { page: number; top: number; bottom: number } | null = null;
  try {
    const pj = JSON.stringify(withPara(host, p));
    const first = ih.wasm.getCursorRectByPath(sel.sec, sel.ppi, pj, 0);
    const len = ih.wasm.getCellParagraphLengthByPath(sel.sec, sel.ppi, pj);
    const last = len > 0 ? ih.wasm.getCursorRectByPath(sel.sec, sel.ppi, pj, len) : first;
    band = { page: first.pageIndex, top: first.y, bottom: last && last.pageIndex === first.pageIndex ? last.y + last.height : first.y + first.height };
  } catch { band = null; }
  if (!band) { clearDropLine(ih); return null; }
  const pointerY = band.page === pi ? py : band.top;
  const dst = pointerY > (band.top + band.bottom) / 2 ? p + 1 : p;
  if (dst === hostPara || dst === hostPara + 1) { clearDropLine(ih); return null; }
  // 선: 그 칸 폭
  let cell: any = null;
  try {
    cell = ih.wasm.getTableCellBboxesByPath(sel.sec, sel.ppi, JSON.stringify(host))
      .find((b: any) => b.cellIdx === host[host.length - 1].cellIndex && b.pageIndex === band!.page);
  } catch { cell = null; }
  const el = lineEl(ih);
  if (el && cell) {
    const left = ih.virtualScroll.getPageLeftResolved(band.page, sc.clientWidth);
    const top = ih.virtualScroll.getPageOffset(band.page);
    const y = dst > p ? band.bottom : band.top;
    el.style.left = `${left + cell.x * zoom}px`;
    el.style.top = `${top + y * zoom - 1}px`;
    el.style.width = `${cell.w * zoom}px`;
    el.style.display = 'block';
  }
  return { dst };
}

/** 고른 표의 쪽 상자. 표 속 표면 그 표의 칸 상자 합집합(getTableBBoxAtPage 는 맨 바깥 표만 돌려준다) */
export function claudeSelectedTableBBox(ih: any, ref: { sec: number; ppi: number; ci: number }, pi: number): { x: number; y: number; width: number; height: number } {
  const sel = ih.cursor.getSelectedTableRef?.();
  if (sel?.cellPath && sel.cellPath.length > 1 && sel.sec === ref.sec && sel.ppi === ref.ppi) {
    const cs = ih.wasm.getTableCellBboxesByPath(ref.sec, ref.ppi, JSON.stringify(sel.cellPath)).filter((b: any) => b.pageIndex === pi);
    if (!cs.length) return { x: 0, y: 0, width: -1, height: -1 };
    const x0 = Math.min(...cs.map((b: any) => b.x));
    const y0 = Math.min(...cs.map((b: any) => b.y));
    return { x: x0, y: y0, width: Math.max(...cs.map((b: any) => b.x + b.w)) - x0, height: Math.max(...cs.map((b: any) => b.y + b.h)) - y0 };
  }
  return ih.wasm.getTableBBoxAtPage(ref.sec, ref.ppi, ref.ci, pi);
}

/** 표 속 표를 같은 칸의 dst 자리로 옮긴다(되돌리기 한 번). 새 표 경로를 돌려준다 */
export function applyCellDrop(ih: any, sel: { sec: number; ppi: number; cellPath: PathEntry[] }, dst: number): PathEntry[] | null {
  let out: PathEntry[] | null = null;
  try {
    ih.executeOperation({
      kind: 'snapshot',
      operationType: 'moveControlInCell',
      operation: (w: any) => {
        const doc = w.doc ?? w;
        const r = JSON.parse(doc.moveControlInCellByPath(sel.sec, sel.ppi, JSON.stringify(sel.cellPath), dst));
        if (r?.ok) {
          const host = withPara(hostCellPath(sel.cellPath), r.cellPara);
          out = [...host, { ...sel.cellPath[sel.cellPath.length - 1] }];
        }
        return { sectionIndex: sel.sec, paragraphIndex: sel.ppi, charOffset: 0 };
      },
    });
  } catch (err) {
    console.warn('[claude move-drop] 표 속 표 옮기기 실패:', err);
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
