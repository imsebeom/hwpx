// 메모와 무관한지 가린다: ① 2쪽을 먼저 본 뒤 3쪽 표를 고르면 상자가 몇 개인가 ② 표를 고른 채 그림을 누르면 표 상자가 지워지는가
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
  return r.result?.result?.value === undefined ? { error: JSON.stringify(r.result?.exceptionDetails ?? r).slice(0, 300) } : JSON.parse(r.result.result.value);
};
const click = async (x, y) => {
  await call('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
  for (const type of ['mousePressed', 'mouseReleased']) await call('Input.dispatchMouseEvent', { type, x, y, button: 'left', clickCount: 1 });
  await new Promise((r) => setTimeout(r, 450));
};
const screenOf = (pageIndex, x, y) => ev(`(async () => { const sc = ih.container.querySelector('#scroll-content'); const zoom = ih.viewportManager.getZoom(); const top = ih.virtualScroll.getPageOffset(${pageIndex}) + ${y} * zoom; ih.container.scrollTop = Math.max(0, top - ih.container.clientHeight / 2); await wait(500); const r = sc.getBoundingClientRect(); const f = document.querySelector('iframe').getBoundingClientRect(); return { x: f.left + r.left + ih.virtualScroll.getPageLeftResolved(${pageIndex}, sc.clientWidth) + ${x} * zoom, y: f.top + r.top + top }; })()`);
const boxes = () => ev(`(() => { const sc = ih.container.querySelector('#scroll-content'); const r0 = sc.getBoundingClientRect(); const layer = sc.querySelector('.table-object-layer'); const big = [...layer.querySelectorAll('*')].filter((e) => e.getClientRects().length && e.getBoundingClientRect().width > 20).map((e) => { const r = e.getBoundingClientRect(); return Math.round(r.left - r0.left) + ',' + Math.round(r.top - r0.top) + ' ' + Math.round(r.width) + 'x' + Math.round(r.height); });
  const c = ih.cursor; return { memo: !!sc.querySelector('.claude-memo-layer'), picture: !!c.isInPictureObjectSelection?.(), table: !!c.isInTableObjectSelection?.(), tableBoxes: big }; })()`);
const all = await ev(`(() => { const d = ih.wasm.doc; const o = []; for (let p = 0; p < d.pageCount(); p++) for (const c of JSON.parse(d.getPageControlLayout(p)).controls) o.push({ page: p, type: c.type, x: c.x, y: c.y, w: c.w, h: c.h, depth: (c.stableIndex?.length ?? 3) / 3 }); return o; })()`);
const table = all.find((c) => c.type === 'table' && c.depth === 1 && c.page === Number(process.argv[3] ?? 2));
const pic = all.find((c) => c.type === 'image');
// ① 2쪽을 화면에 올려 그린 뒤 3쪽 표의 왼쪽 선을 누른다
await screenOf(1, 300, 500);
const b = await screenOf(table.page, table.x, table.y + 60);
await click(b.x, b.y);
console.log(process.argv[2] ?? '', `① ${table.page + 1}쪽 표를 고름:`, JSON.stringify(await boxes()));
// ② 표를 고른 채 2쪽 그림을 누른다
const p = await screenOf(pic.page, pic.x + pic.w / 2, pic.y + pic.h / 2);
await click(p.x, p.y);
console.log('   ② 그 상태에서 그림을 누름:', JSON.stringify(await boxes()));
const t = await screenOf(0, 300, 200);
await click(t.x, t.y);
console.log('   ③ 1쪽 글을 누름:', JSON.stringify(await boxes()));
ws.close();
