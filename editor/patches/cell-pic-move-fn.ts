
// [claude-hwpx cell-pic-move] 칸 안 글자처럼 취급 그림 끌어 옮기기(위 updatePictureMoveDrag, finishPictureMoveDrag 에서 부른다).
// 엔진 convertCaretOffset 모드 7(컨트롤 번호 → 캐럿 칸, 엔진 패치 cell-pic-caret)로 그림 자리를 찾고, 캐럿 축 복사, 삭제,
// 붙여넣기를 한 스냅샷에서 한다. 놓는 자리는 본문 문단이나 다른 칸(표 속 표 칸 포함)도 된다
const CLAUDE_CELL_PIC_LINE = 'claude-cell-pic-drop';

function claudeCellPicDropClear(ih: any): void {
  const el = ih.container.querySelector(`#${CLAUDE_CELL_PIC_LINE}`) as HTMLElement | null;
  if (el) el.style.display = 'none';
}

function claudeCellPicDropUpdate(ih: any, e: MouseEvent): any {
  let hit: any = null;
  try { hit = ih.hitTestFromEvent?.(e) ?? null; } catch { hit = null; }
  const sc = ih.container.querySelector('#scroll-content') as HTMLElement | null;
  const r = hit?.cursorRect;
  if (!hit || !sc || !r || hit.isTextBox) { claudeCellPicDropClear(ih); return null; }
  let el = sc.querySelector(`#${CLAUDE_CELL_PIC_LINE}`) as HTMLDivElement | null;
  if (!el) {
    el = document.createElement('div');
    el.id = CLAUDE_CELL_PIC_LINE;
    el.style.cssText = 'position:absolute;width:2px;background:#1e6fff;pointer-events:none;z-index:30;display:none;';
    sc.appendChild(el);
  }
  const zoom = ih.viewportManager.getZoom();
  const left = ih.virtualScroll.getPageLeftResolved(r.pageIndex, sc.clientWidth);
  const top = ih.virtualScroll.getPageOffset(r.pageIndex);
  el.style.left = `${left + r.x * zoom - 1}px`;
  el.style.top = `${top + r.y * zoom}px`;
  el.style.height = `${Math.max(8, r.height * zoom)}px`;
  el.style.display = 'block';
  return hit;
}

function claudeCellPicMove(ih: any, ref: any, hit: any): void {
  const doc = ih.wasm.doc;
  const src = ref.cellPath as Array<{ controlIndex: number; cellIndex: number; cellParaIndex: number }>;
  const srcJson = JSON.stringify(src);
  const srcCpi = src[src.length - 1].cellParaIndex;
  let off: number;
  try { off = doc.convertCaretOffset(ref.sec, ref.ppi, srcJson, ref.ci, 7); } catch { return; }
  const destInCell = (hit.cellPath?.length ?? 0) > 0 && hit.parentParaIndex !== undefined;
  const destJson = destInCell ? JSON.stringify(hit.cellPath) : '';
  let destOff = hit.charOffset ?? 0;
  const samePara = destInCell && hit.sectionIndex === ref.sec && hit.parentParaIndex === ref.ppi && destJson === srcJson;
  if (samePara && (destOff === off || destOff === off + 1)) return;   // 제자리
  if (samePara && destOff > off) destOff -= 1;                        // 그림을 빼면 뒤 칸이 하나 당겨진다
  try {
    ih.executeOperation({
      kind: 'snapshot',
      operationType: 'movePicture',
      operation: (wasm: any) => {
        const d = wasm.doc;
        d.copySelectionCaretInCellByPath(ref.sec, ref.ppi, srcJson, srcCpi, off, srcCpi, off + 1);
        d.deleteRangeCaretInCellByPath(ref.sec, ref.ppi, srcJson, srcCpi, off, srcCpi, off + 1);
        if (destInCell) d.pasteInternalInCellByPath(hit.sectionIndex, hit.parentParaIndex, destJson, destOff);
        else d.pasteInternal(hit.sectionIndex, hit.paragraphIndex, destOff);
        return { ...hit, charOffset: destOff + 1 };
      },
    });
    ih.cursor.exitPictureObjectSelection?.();
    ih.pictureObjectRenderer?.clear();
    ih.eventBus.emit('picture-object-selection-changed', false);
  } catch (err) {
    console.warn('[claude-hwpx cell-pic-move] 칸 그림 옮기기 실패:', err);
  }
}
