
// [claude-hwpx nested-table-table] 표 속 표의 크기 조절. 표 참조(끌기 상태의 path, 칸 문맥의 cellPath)가 깊이 2 이상이면
// 칸 속성 조회, 칸 상자, 크기 적용을 칸 경로 API 로 보낸다. 평면 API 는 (구역, 문단, 컨트롤)로 맨 바깥 표만 가리켜
// 안쪽 표 테두리를 끌어도 바깥 표가 바뀌거나 아무 일도 없었다. setup.mjs 가 이 파일의 평면 호출을 아래 함수로 바꾼다
function claudeNestedPath(ref: any): any[] | undefined {
  const p = ref?.path ?? ref?.cellPath;
  return Array.isArray(p) && p.length > 1 ? p : undefined;
}

function claudeCellProps(wasm: any, ref: any, cellIdx: number): any {
  const p = claudeNestedPath(ref);
  return p
    ? wasm.getCellPropertiesByPath(ref.sec, ref.ppi, JSON.stringify(p), cellIdx)
    : wasm.getCellProperties(ref.sec, ref.ppi, ref.ci, cellIdx);
}

function claudeTableBboxes(wasm: any, ref: any): any[] {
  const p = claudeNestedPath(ref);
  return p
    ? wasm.getTableCellBboxesByPath(ref.sec, ref.ppi, JSON.stringify(p))
    : wasm.getTableCellBboxes(ref.sec, ref.ppi, ref.ci);
}

function claudeResizeCells(wasm: any, ref: any, updates: any[]): void {
  const p = claudeNestedPath(ref);
  if (p) wasm.resizeTableCellsByPath(ref.sec, ref.ppi, JSON.stringify(p), updates);
  else wasm.resizeTableCells(ref.sec, ref.ppi, ref.ci, updates);
}
