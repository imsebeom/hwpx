// 에디터에서 표 속 표 칸의 그림을 손잡이로 끌어 줄인 뒤 그림, 상자, 다음 문단 자리를 본다(hold.py 로 CDP 9333): node pic_drag.mjs [배율=0.6]
const scale = Number(process.argv[2] ?? 0.6);
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
  return r.result?.result?.value === undefined ? { error: JSON.stringify(r.result?.exceptionDetails ?? r).slice(0, 400) } : JSON.parse(r.result.result.value);
};
const mouse = async (type, x, y) => call('Input.dispatchMouseEvent', { type, x, y, button: 'left', clickCount: type === 'mouseMoved' ? 0 : 1 });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const geom = () => ev(`(async () => { const sc = ih.container.querySelector('#scroll-content'); const zoom = ih.viewportManager.getZoom(); const d = ih.wasm.doc; const l = JSON.parse(d.getPageControlLayout(1)).controls;
  const pic = l.find((c) => c.type === 'image'); const tbl = l.find((c) => c.type === 'table' && c.stableIndex.length === 9 && c.paraIdx === 7);
  const top = ih.virtualScroll.getPageOffset(1) + pic.y * zoom; ih.container.scrollTop = Math.max(0, top - ih.container.clientHeight / 2); await wait(400);
  const r = sc.getBoundingClientRect(); const f = document.querySelector('iframe').getBoundingClientRect();
  const left = f.left + r.left + ih.virtualScroll.getPageLeftResolved(1, sc.clientWidth); const ptop = f.top + r.top + ih.virtualScroll.getPageOffset(1);
  const nextPath = JSON.stringify([{ controlIndex: 0, cellIndex: 0, cellParaIndex: 7 }, { controlIndex: 0, cellIndex: 0, cellParaIndex: 1 }]);
  let next = null; try { next = JSON.parse(d.getCursorRectByPath(0, 3, nextPath, 0)).y; } catch {}
  return { zoom, left, ptop, pic: { x: pic.x, y: pic.y, w: pic.w, h: pic.h }, tbl: tbl ? { y: tbl.y, h: tbl.h } : null, next, pages: d.pageCount() }; })()`);
const show = (label, g) => console.log(`${label} 그림 ${g.pic.y.toFixed(1)}~${(g.pic.y + g.pic.h).toFixed(1)} h${g.pic.h.toFixed(1)} | 그래프 표 h${g.tbl?.h?.toFixed(1)} | 다음 문단 y ${g.next?.toFixed?.(1)} | 쪽수 ${g.pages}`);
let g = await geom();
show('전 ', g);
// 그림 가운데를 눌러 고른다
const cx = g.left + (g.pic.x + g.pic.w / 2) * g.zoom, cy = g.ptop + (g.pic.y + g.pic.h / 2) * g.zoom;
await mouse('mouseMoved', cx, cy); await mouse('mousePressed', cx, cy); await mouse('mouseReleased', cx, cy); await sleep(400);
const sel = await ev(`({ picture: !!ih.cursor.isInPictureObjectSelection?.() })`);
console.log('그림 선택', sel.picture);
// 오른쪽 아래 손잡이를 끌어 줄인다
const hx = g.left + (g.pic.x + g.pic.w) * g.zoom, hy = g.ptop + (g.pic.y + g.pic.h) * g.zoom;
const tx = g.left + (g.pic.x + g.pic.w * scale) * g.zoom, ty = g.ptop + (g.pic.y + g.pic.h * scale) * g.zoom;
await mouse('mouseMoved', hx, hy); await sleep(100); await mouse('mousePressed', hx, hy); await sleep(100);
for (let i = 1; i <= 8; i++) { await mouse('mouseMoved', hx + (tx - hx) * i / 8, hy + (ty - hy) * i / 8); await sleep(40); }
await mouse('mouseReleased', tx, ty); await sleep(800);
g = await geom();
show(`${scale * 100}%`, g);
ws.close();
