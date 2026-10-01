// ==== find ====
export interface TableRef {
  sec: number;
  ppi: number;
  ci: number;
}
// ==== replace ====
export interface CellPathStep {
  controlIndex: number;
  cellIndex: number;
  cellParaIndex: number;
}

export interface TableRef {
  sec: number;
  ppi: number;
  ci: number;
  /**
   * [claude-hwpx nested-table-cache] hitTest 의 칸 경로. 깊이 2 이상이면 표 속 표다.
   * sec/ppi/ci 는 맨 바깥 표만 가리켜, 경로를 빼면 표 속 표 위에서도 바깥 표 괘선만 캐시에 들어왔다(상류 #7214, #7442).
   */
  path?: readonly CellPathStep[];
}

/** 캐시 신원. 경로의 마지막 마디는 그 표 안 커서 자리라 컨트롤 번호만 쓴다(칸을 옮겨도 같은 표로 본다). */
export function tableIdentity(tableRef: TableRef): string {
  const base = `${tableRef.sec}:${tableRef.ppi}:${tableRef.ci}`;
  const path = tableRef.path;
  if (!path || path.length <= 1) return base;
  return `${base}|${path.map((s, i) => i === path.length - 1
    ? `${s.controlIndex}`
    : `${s.controlIndex}.${s.cellIndex}.${s.cellParaIndex}`).join('/')}`;
}

/** hitTest 의 칸 경로가 ctxPath 와 같은 표 속 표를 가리키는가(마지막 마디는 컨트롤 번호만 비교). */
export function isSameNestedTablePath(
  ctxPath: readonly CellPathStep[] | undefined,
  hitPath: readonly CellPathStep[] | undefined,
): boolean {
  if (!ctxPath || ctxPath.length < 2 || !hitPath || ctxPath.length !== hitPath.length) return false;
  for (let i = 0; i < ctxPath.length - 1; i++) {
    const a = ctxPath[i];
    const b = hitPath[i];
    if (a.controlIndex !== b.controlIndex || a.cellIndex !== b.cellIndex || a.cellParaIndex !== b.cellParaIndex) return false;
  }
  return ctxPath[ctxPath.length - 1].controlIndex === hitPath[hitPath.length - 1].controlIndex;
}
// ==== next ====
    getTableCellBboxes(sec: number, ppi: number, ci: number, pageHint?: number): B[];
  };
// ==== replace ====
    getTableCellBboxes(sec: number, ppi: number, ci: number, pageHint?: number): B[];
    getTableCellBboxesByPath(sec: number, ppi: number, pathJson: string): B[];
  };
// ==== next ====
function sameTable(a: TableRef, b: TableRef): boolean {
  return a.sec === b.sec && a.ppi === b.ppi && a.ci === b.ci;
}

function failureKey(tableRef: TableRef, pageIdx: number): string {
  return `${tableRef.sec}:${tableRef.ppi}:${tableRef.ci}:${pageIdx}`;
}
// ==== replace ====
function sameTable(a: TableRef, b: TableRef): boolean {
  return tableIdentity(a) === tableIdentity(b);
}

function failureKey(tableRef: TableRef, pageIdx: number): string {
  return `${tableIdentity(tableRef)}:${pageIdx}`;
}
// ==== next ====
    const bboxes = host.wasm.getTableCellBboxes(tableRef.sec, tableRef.ppi, tableRef.ci, pageIdx);
// ==== replace ====
    const path = tableRef.path;
    const bboxes = path && path.length > 1
      ? host.wasm.getTableCellBboxesByPath(tableRef.sec, tableRef.ppi, JSON.stringify(path))
      : host.wasm.getTableCellBboxes(tableRef.sec, tableRef.ppi, tableRef.ci, pageIdx);
