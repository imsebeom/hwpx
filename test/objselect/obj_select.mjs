// 메모 패널을 연 상태와 닫은 상태에서 그림, 표 개체 선택을 비교한다(hold.py 로 CDP 9333 이 열려 있어야 한다).
//   node obj_select.mjs list            쪽마다 개체 종류와 자리
//   node obj_select.mjs run             패널 열림, 닫힘에서 그림 누르기와 표 선 누르기
const targets = await (await fetch('http://127.0.0.1:9333/json')).json();
const page = targets.find((t) => t.type === 'page' && !t.url.includes('studio'));
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener('open', r));
let id = 0;
const call = (method, params = {}) => new Promise((res) => {
  const my = ++id;
  const on = (m) => { const msg = JSON.parse(m.data); if (msg.id === my) { ws.removeEventListener('message', on); res(msg); } };
  ws.addEventListener('message', on);
  ws.send(JSON.stringify({ id: my, method, params }));
});
const ev = async (expr) => {
  const wrapped = `(async () => { const S = document.querySelector('iframe').contentWindow; const D = S.document; const ih = S.__claudeIH(); const wait = (ms) => new Promise((r) => setTimeout(r, ms)); return JSON.stringify(await (${expr})); })()`;
  const r = await call('Runtime.evaluate', { expression: wrapped, awaitPromise: true });
  if (r.result?.result?.value === undefined) return { error: JSON.stringify(r.result?.exceptionDetails ?? r).slice(0, 400) };
  return JSON.parse(r.result.result.value);
};
const click = async (x, y) => {
  await call('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
  for (const type of ['mousePressed', 'mouseReleased']) await call('Input.dispatchMouseEvent', { type, x, y, button: 'left', clickCount: 1 });
};
const controls = () => ev(`(() => { const d = ih.wasm.doc; const out = []; for (let p = 0; p < d.pageCount(); p++) for (const c of JSON.parse(d.getPageControlLayout(p)).controls) out.push({ page: p, type: c.type, x: c.x, y: c.y, w: c.w, h: c.h, para: c.paraIdx, ctrl: c.controlIdx, depth: (c.stableIndex?.length ?? 3) / 3 }); return out; })()`);
// 쪽 좌표 → 호스트 화면 좌표(그 자리가 보이게 먼저 스크롤한다)
const toScreen = (pageIndex, x, y) => ev(`(async () => {
  const sc = ih.container.querySelector('#scroll-content');
  const zoom = ih.viewportManager.getZoom();
  const top = ih.virtualScroll.getPageOffset(${pageIndex}) + ${y} * zoom;
  ih.container.scrollTop = Math.max(0, top - ih.container.clientHeight / 2);
  await wait(400);
  const r = sc.getBoundingClientRect();
  const f = document.querySelector('iframe').getBoundingClientRect();
  return { x: f.left + r.left + ih.virtualScroll.getPageLeftResolved(${pageIndex}, sc.clientWidth) + ${x} * zoom, y: f.top + r.top + top, zoom };
})()`);
const state = () => ev(`(() => { const c = ih.cursor; const pic = c.isInPictureObjectSelection?.() ? c.getSelectedPictureRef?.() : null; const tbl = c.isInTableObjectSelection?.() ? c.getSelectedTableRef?.() : null; const pos = ih.getCursorPosition();
  return { picture: pic ? { type: pic.type, ppi: pic.ppi, ci: pic.ci, cell: pic.cellIdx ?? null } : null, table: tbl ? { para: tbl.parentParaIndex ?? tbl.ppi ?? tbl.paraIdx, ctrl: tbl.controlIndex ?? tbl.ci, path: tbl.cellPath?.length ?? 0 } : null,
    cursor: { p: pos.paragraphIndex, off: pos.charOffset, cell: pos.cellIndex ?? null }, panel: !!D.querySelector('.claude-memo-panel'), hl: D.querySelectorAll('.claude-memo-hl').length }; })()`);
const escape = () => ev(`(ih.cursor.clearSelection?.(), ih.cursor.exitPictureObjectSelection?.(), ih.cursor.exitTableObjectSelection?.(), ih.updateCaret?.(true), 1)`);
const setPanel = (on) => ev(`(async () => { const shown = !!D.querySelector('.claude-memo-panel'); if (shown !== ${on}) D.getElementById('tb-claude-memo').click(); await wait(900); return !!D.querySelector('.claude-memo-panel'); })()`);

const all = await controls();
if (process.argv[2] === 'list') {
  for (const c of all) console.log(`쪽 ${c.page + 1} ${c.type.padEnd(8)} x ${c.x} y ${c.y} w ${c.w} h ${c.h} 문단 ${c.para} 깊이 ${c.depth}`);
} else {
  const pics = all.filter((c) => /image|picture|shape/i.test(c.type));
  const tables = all.filter((c) => c.type === 'table');
  const cases = [
    ...pics.slice(0, 3).map((c, i) => ({ name: `그림 ${i + 1}(쪽 ${c.page + 1}) 가운데`, page: c.page, x: c.x + c.w / 2, y: c.y + c.h / 2, want: 'picture' })),
    ...tables.slice(0, 4).map((c, i) => ({ name: `표 ${i + 1}(쪽 ${c.page + 1}, 깊이 ${c.depth}) 왼쪽 선`, page: c.page, x: c.x, y: c.y + Math.min(c.h / 2, 40), want: 'table' })),
    ...tables.slice(0, 2).map((c, i) => ({ name: `표 ${i + 1}(쪽 ${c.page + 1}) 칸 안`, page: c.page, x: c.x + 30, y: c.y + Math.min(c.h / 2, 20), want: 'cursor' })),
  ];
  const results = {};
  const order = process.argv[3] === 'closed' ? [false, true, false, true] : [true, false, true, false];
  let round = 0;
  for (const on of order) {
    const shown = await setPanel(on);
    const key = `${++round}회 ${shown ? '패널 열림' : '패널 닫힘'}`;
    results[key] = [];
    for (const c of cases) {
      await escape();
      const p = await toScreen(c.page, c.x, c.y);
      await click(p.x, p.y);
      await new Promise((r) => setTimeout(r, 350));
      const s = await state();
      results[key].push({ name: c.name, got: s.picture ? `그림(문단 ${s.picture.ppi})` : s.table ? `표(문단 ${s.table.para}, 경로 ${s.table.path})` : `커서(p${s.cursor.p}, 칸 ${s.cursor.cell}, ${s.cursor.off})`, at: `${Math.round(p.x)},${Math.round(p.y)}` });
    }
  }
  const keys = Object.keys(results);
  for (let i = 0; i < cases.length; i++) {
    const row = keys.map((k) => `${k}: ${results[k][i].got} @${results[k][i].at}`);
    const same = new Set(keys.map((k) => results[k][i].got)).size === 1;
    console.log(`${same ? '같음' : '다름'}  ${cases[i].name}\n      ${row.join('\n      ')}`);
  }
}
ws.close();
