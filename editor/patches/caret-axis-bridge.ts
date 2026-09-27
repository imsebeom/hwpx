
// [claude-hwpx caret-axis] 캐럿 축 연결.
// 스튜디오의 캐럿 위치(charOffset)는 캐럿 축(글자처럼 취급 개체, 각주, 미주도 한 칸)인데, 엔진의 글자 편집
// 함수 다수는 글자 축을 받는다. 개체 뒤에서 입력, 삭제, 글자 모양, 셀 글 읽기가 한 칸씩 어긋났다.
// 여기서 호출 직전에 캐럿 축을 그 함수의 축으로 바꾸고(엔진 convertCaretOffset), 선택 삭제와 복사는 범위 안
// 개체까지 다루는 캐럿 축 함수(deleteRangeCaret*, copySelectionCaret*)로 보낸다. 선택 음영(getSelectionRects*)과
// 캐럿 좌표는 엔진이 캐럿 축으로 계산하므로 그대로 둔다. 붙여넣기는 엔진이 캐럿 축으로 받는다.
{
  type AnyFn = (...args: any[]) => any;
  const proto = WasmBridge.prototype as any;
  const docOf = (bridge: any): any => bridge.doc;
  const hasAxis = (bridge: any): boolean => typeof docOf(bridge)?.convertCaretOffset === 'function';
  /** mode: 0 캐럿→글자, 2 캐럿→나누기, 4 개체 바로 뒤인가, 5 캐럿 축 길이 */
  const conv = (bridge: any, sec: number, para: number, path: string, off: number, mode: number): number => {
    try {
      return docOf(bridge).convertCaretOffset(sec, para, path, Math.max(0, off), mode);
    } catch {
      return off;
    }
  };
  const flatPath = (ci: number, cell: number, cpi: number): string =>
    JSON.stringify([{ controlIndex: ci, cellIndex: cell, cellParaIndex: cpi }]);
  const pathAt = (pathJson: string, cpi: number): string => {
    const path = JSON.parse(pathJson);
    if (path.length) path[path.length - 1].cellParaIndex = cpi;
    return JSON.stringify(path);
  };
  const wrap = (name: string, make: (orig: AnyFn) => AnyFn): void => {
    const orig = proto[name];
    if (typeof orig !== 'function') return;
    proto[name] = function (this: any, ...args: any[]) {
      if (!hasAxis(this)) return orig.apply(this, args);
      return make(orig).apply(this, args);
    };
  };
  /** [off, off+count) 캐럿 범위 → [글자 시작, 글자 개수] */
  const textRange = (bridge: any, sec: number, para: number, path: string, off: number, count: number): [number, number] => {
    const a = conv(bridge, sec, para, path, off, 0);
    const b = conv(bridge, sec, para, path, off + count, 0);
    return [a, Math.max(0, b - a)];
  };
  /** 삽입: 글자 축으로 바꾸고, 캐럿이 개체 바로 뒤면 엔진 표지를 켜 개체 뒤에 넣게 한다 */
  const withAfter = <T>(bridge: any, sec: number, para: number, path: string, off: number, run: (t: number) => T): T => {
    const t = conv(bridge, sec, para, path, off, 0);
    const after = conv(bridge, sec, para, path, off, 4) === 1;
    const doc = docOf(bridge);
    if (after) doc.setInsertAfterInline?.(true);
    try {
      return run(t);
    } finally {
      if (after) doc.setInsertAfterInline?.(false);
    }
  };
  const graphemes = (text: string): number => [...text].length;
  const withCaret = <T extends { charOffset?: number }>(result: T, caret: number): T =>
    result && typeof result === 'object' && 'charOffset' in result ? { ...result, charOffset: caret } : result;

  /** 캐럿 칸 [off, off+1) 이 글자가 아니라 개체(글자처럼 취급 개체, 각주, 미주)인가 — Backspace, Delete 가 쓴다 */
  proto.isCaretControlSlot = function (this: any, pos: any): boolean {
    if (!hasAxis(this) || pos.isTextBox) return false;
    const inCell = pos.parentParaIndex !== undefined && (pos.cellPath?.length ?? 0) > 0;
    const para = inCell ? pos.parentParaIndex : pos.paragraphIndex;
    const path = inCell ? JSON.stringify(pos.cellPath) : '';
    const off = pos.charOffset;
    if (off < 0 || off >= conv(this, pos.sectionIndex, para, path, 0, 5)) return false;
    return conv(this, pos.sectionIndex, para, path, off, 0) === conv(this, pos.sectionIndex, para, path, off + 1, 0);
  };

  // ── 본문 ──
  wrap('insertText', (orig) => function (this: any, sec: number, para: number, off: number, text: string) {
    return withAfter(this, sec, para, '', off, (t) => orig.call(this, sec, para, t, text));
  });
  wrap('replaceBodyTextLocal', (orig) => function (this: any, sec: number, para: number, off: number, del: number, text: string) {
    const [t, n] = textRange(this, sec, para, '', off, del);
    const result = withAfter(this, sec, para, '', off, () => orig.call(this, sec, para, t, n, text));
    return withCaret(result, off + graphemes(text));
  });
  wrap('deleteText', (orig) => function (this: any, sec: number, para: number, off: number, count: number) {
    const [t, n] = textRange(this, sec, para, '', off, count);
    return orig.call(this, sec, para, t, n);
  });
  wrap('getTextRange', (orig) => function (this: any, sec: number, para: number, off: number, count: number) {
    const [t, n] = textRange(this, sec, para, '', off, count);
    return orig.call(this, sec, para, t, n);
  });
  wrap('getParagraphLength', () => function (this: any, sec: number, para: number) {
    return conv(this, sec, para, '', 0, 5);
  });
  for (const name of ['splitParagraph', 'insertPageBreak', 'insertColumnBreak']) {
    wrap(name, (orig) => function (this: any, sec: number, para: number, off: number, ...rest: any[]) {
      return orig.call(this, sec, para, conv(this, sec, para, '', off, 2), ...rest);
    });
  }
  wrap('deleteRange', (orig) => function (this: any, sec: number, sp: number, so: number, ep: number, eo: number) {
    const doc = docOf(this);
    if (typeof doc.deleteRangeCaret !== 'function') return orig.call(this, sec, sp, so, ep, eo);
    return JSON.parse(doc.deleteRangeCaret(sec, sp, so, ep, eo));
  });
  wrap('copySelection', (orig) => function (this: any, sec: number, sp: number, so: number, ep: number, eo: number) {
    const doc = docOf(this);
    if (typeof doc.copySelectionCaret !== 'function') return orig.call(this, sec, sp, so, ep, eo);
    return doc.copySelectionCaret(sec, sp, so, ep, eo);
  });
  wrap('exportSelectionHtml', (orig) => function (this: any, sec: number, sp: number, so: number, ep: number, eo: number) {
    return orig.call(this, sec, sp, conv(this, sec, sp, '', so, 0), ep, conv(this, sec, ep, '', eo, 0));
  });
  wrap('getCharPropertiesAt', (orig) => function (this: any, sec: number, para: number, off: number) {
    return orig.call(this, sec, para, conv(this, sec, para, '', off, 0));
  });
  for (const name of ['applyCharFormat', 'setCharShapeId']) {
    wrap(name, (orig) => function (this: any, sec: number, para: number, s: number, e: number, arg: any) {
      return orig.call(this, sec, para, conv(this, sec, para, '', s, 0), conv(this, sec, para, '', e, 0), arg);
    });
  }

  // ── 셀(평면 좌표) ──
  for (const name of ['insertTextInCell', 'insertTextInCellDeferredPagination']) {
    wrap(name, (orig) => function (this: any, sec: number, ppi: number, ci: number, cell: number, cpi: number, off: number, text: string) {
      const result = withAfter(this, sec, ppi, flatPath(ci, cell, cpi), off, (t) => orig.call(this, sec, ppi, ci, cell, cpi, t, text));
      return withCaret(result, off + graphemes(text));
    });
  }
  for (const name of ['deleteTextInCell', 'deleteTextInCellDeferredPagination', 'getTextInCell']) {
    wrap(name, (orig) => function (this: any, sec: number, ppi: number, ci: number, cell: number, cpi: number, off: number, count: number) {
      const [t, n] = textRange(this, sec, ppi, flatPath(ci, cell, cpi), off, count);
      return withCaret(orig.call(this, sec, ppi, ci, cell, cpi, t, n), off);
    });
  }
  wrap('replaceTextInCellDeferredPagination', (orig) => function (this: any, sec: number, ppi: number, ci: number, cell: number, cpi: number, off: number, del: number, text: string) {
    const path = flatPath(ci, cell, cpi);
    const [t, n] = textRange(this, sec, ppi, path, off, del);
    const result = withAfter(this, sec, ppi, path, off, () => orig.call(this, sec, ppi, ci, cell, cpi, t, n, text));
    return withCaret(result, off + graphemes(text));
  });
  wrap('getCellParagraphLength', () => function (this: any, sec: number, ppi: number, ci: number, cell: number, cpi: number) {
    return conv(this, sec, ppi, flatPath(ci, cell, cpi), 0, 5);
  });
  wrap('splitParagraphInCell', (orig) => function (this: any, sec: number, ppi: number, ci: number, cell: number, cpi: number, off: number, ...rest: any[]) {
    return orig.call(this, sec, ppi, ci, cell, cpi, conv(this, sec, ppi, flatPath(ci, cell, cpi), off, 2), ...rest);
  });
  wrap('deleteRangeInCell', (orig) => function (this: any, sec: number, ppi: number, ci: number, cell: number, sp: number, so: number, ep: number, eo: number) {
    const doc = docOf(this);
    if (typeof doc.deleteRangeCaretInCell !== 'function') return orig.call(this, sec, ppi, ci, cell, sp, so, ep, eo);
    return JSON.parse(doc.deleteRangeCaretInCell(sec, ppi, ci, cell, sp, so, ep, eo));
  });
  wrap('copySelectionInCell', (orig) => function (this: any, sec: number, ppi: number, ci: number, cell: number, sp: number, so: number, ep: number, eo: number) {
    const doc = docOf(this);
    if (typeof doc.copySelectionCaretInCell !== 'function') return orig.call(this, sec, ppi, ci, cell, sp, so, ep, eo);
    return doc.copySelectionCaretInCell(sec, ppi, ci, cell, sp, so, ep, eo);
  });
  wrap('exportSelectionInCellHtml', (orig) => function (this: any, sec: number, ppi: number, ci: number, cell: number, sp: number, so: number, ep: number, eo: number) {
    return orig.call(this, sec, ppi, ci, cell,
      sp, conv(this, sec, ppi, flatPath(ci, cell, sp), so, 0),
      ep, conv(this, sec, ppi, flatPath(ci, cell, ep), eo, 0));
  });
  wrap('getCellCharPropertiesAt', (orig) => function (this: any, sec: number, ppi: number, ci: number, cell: number, cpi: number, off: number) {
    return orig.call(this, sec, ppi, ci, cell, cpi, conv(this, sec, ppi, flatPath(ci, cell, cpi), off, 0));
  });
  for (const name of ['applyCharFormatInCell', 'setCharShapeIdInCell']) {
    wrap(name, (orig) => function (this: any, sec: number, ppi: number, ci: number, cell: number, cpi: number, s: number, e: number, arg: any) {
      const path = flatPath(ci, cell, cpi);
      return orig.call(this, sec, ppi, ci, cell, cpi, conv(this, sec, ppi, path, s, 0), conv(this, sec, ppi, path, e, 0), arg);
    });
  }

  // ── 셀(경로) ──
  wrap('insertTextInCellByPath', (orig) => function (this: any, sec: number, ppi: number, pathJson: string, off: number, text: string) {
    return withAfter(this, sec, ppi, pathJson, off, (t) => orig.call(this, sec, ppi, pathJson, t, text));
  });
  for (const name of ['deleteTextInCellByPath', 'getTextInCellByPath']) {
    wrap(name, (orig) => function (this: any, sec: number, ppi: number, pathJson: string, off: number, count: number) {
      const [t, n] = textRange(this, sec, ppi, pathJson, off, count);
      return orig.call(this, sec, ppi, pathJson, t, n);
    });
  }
  wrap('getCellParagraphLengthByPath', () => function (this: any, sec: number, ppi: number, pathJson: string) {
    return conv(this, sec, ppi, pathJson, 0, 5);
  });
  wrap('splitParagraphInCellByPath', (orig) => function (this: any, sec: number, ppi: number, pathJson: string, off: number, ...rest: any[]) {
    return orig.call(this, sec, ppi, pathJson, conv(this, sec, ppi, pathJson, off, 2), ...rest);
  });
  wrap('deleteRangeInCellByPath', (orig) => function (this: any, sec: number, ppi: number, pathJson: string, sp: number, so: number, ep: number, eo: number) {
    const doc = docOf(this);
    if (typeof doc.deleteRangeCaretInCellByPath !== 'function') return orig.call(this, sec, ppi, pathJson, sp, so, ep, eo);
    return doc.deleteRangeCaretInCellByPath(sec, ppi, pathJson, sp, so, ep, eo);
  });
  wrap('copySelectionInCellByPath', (orig) => function (this: any, sec: number, ppi: number, pathJson: string, sp: number, so: number, ep: number, eo: number) {
    const doc = docOf(this);
    if (typeof doc.copySelectionCaretInCellByPath !== 'function') return orig.call(this, sec, ppi, pathJson, sp, so, ep, eo);
    return doc.copySelectionCaretInCellByPath(sec, ppi, pathJson, sp, so, ep, eo);
  });
  wrap('exportSelectionInCellHtmlByPath', (orig) => function (this: any, sec: number, ppi: number, pathJson: string, sp: number, so: number, ep: number, eo: number) {
    return orig.call(this, sec, ppi, pathJson,
      sp, conv(this, sec, ppi, pathAt(pathJson, sp), so, 0),
      ep, conv(this, sec, ppi, pathAt(pathJson, ep), eo, 0));
  });
  wrap('getCellCharPropertiesAtByPath', (orig) => function (this: any, sec: number, ppi: number, pathJson: string, off: number) {
    return orig.call(this, sec, ppi, pathJson, conv(this, sec, ppi, pathJson, off, 0));
  });
  for (const name of ['applyCharFormatInCellByPath', 'setCharShapeIdInCellByPath']) {
    wrap(name, (orig) => function (this: any, sec: number, ppi: number, pathJson: string, s: number, e: number, arg: any) {
      return orig.call(this, sec, ppi, pathJson, conv(this, sec, ppi, pathJson, s, 0), conv(this, sec, ppi, pathJson, e, 0), arg);
    });
  }
}
