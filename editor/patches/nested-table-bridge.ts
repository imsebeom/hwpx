
// [claude-hwpx nested-table-bridge] 표 속 표의 칸 크기 조절과 칸 속성 조회(엔진 패치 nested-table-wasm 과 짝)
{
  const proto = WasmBridge.prototype as any;
  proto.getCellPropertiesByPath = function (this: any, sec: number, ppi: number, pathJson: string, cellIdx: number) {
    return JSON.parse(this.doc.getCellPropertiesByPath(sec, ppi, pathJson, cellIdx));
  };
  proto.resizeTableCellsByPath = function (this: any, sec: number, ppi: number, pathJson: string, updates: unknown[]) {
    return JSON.parse(this.doc.resizeTableCellsByPath(sec, ppi, pathJson, JSON.stringify(updates)));
  };
}
