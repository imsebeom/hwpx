// 그림을 누른 뒤 표 개체 층, 그림 손잡이 층에 무엇이 그려지는지 패널 열림/닫힘에서 비교한다: node obj_layers.mjs
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
const key = async (k, code, vk) => {
  await call('Input.dispatchKeyEvent', { type: 'rawKeyDown', key: k, code, windowsVirtualKeyCode: vk });
  await call('Input.dispatchKeyEvent', { type: 'keyUp', key: k, code, windowsVirtualKeyCode: vk });
  await new Promise((r) => setTimeout(r, 250));
};
const screenOf = (pageIndex, x, y, cy) => ev(`(async () => { const sc = ih.container.querySelector('#scroll-content'); const zoom = ih.viewportManager.getZoom(); const top = ih.virtualScroll.getPageOffset(${pageIndex}) + ${cy} * zoom; ih.container.scrollTop = Math.max(0, top - ih.container.clientHeight / 2); await wait(400); const r = sc.getBoundingClientRect(); const f = document.querySelector('iframe').getBoundingClientRect(); return { x: f.left + r.left + ih.virtualScroll.getPageLeftResolved(${pageIndex}, sc.clientWidth) + ${x} * zoom, y: f.top + r.top + ih.virtualScroll.getPageOffset(${pageIndex}) + ${y} * zoom }; })()`);
// 개체 층의 보이는 조각을 쪽 좌표로(패널 유무와 무관하게 비교하려고 쪽 왼쪽을 뺀다)
const layers = (pageIndex) => ev(`(() => { const sc = ih.container.querySelector('#scroll-content'); const zoom = ih.viewportManager.getZoom(); const r0 = sc.getBoundingClientRect(); const left = r0.left + ih.virtualScroll.getPageLeftResolved(${pageIndex}, sc.clientWidth); const top = r0.top + ih.virtualScroll.getPageOffset(${pageIndex});
  const out = {}; for (const layer of sc.querySelectorAll(':scope > div')) { if (layer.className.includes('claude-memo')) continue; const kids = [...layer.querySelectorAll('*')].filter((e) => e.getClientRects().length && getComputedStyle(e).display !== 'none'); if (!kids.length) continue;
    out[layer.className || '(이름 없음)'] = kids.map((e) => { const r = e.getBoundingClientRect(); return Math.round((r.left - left) / zoom) + ',' + Math.round((r.top - top) / zoom) + ' ' + Math.round(r.width / zoom) + 'x' + Math.round(r.height / zoom); }).slice(0, 24); }
  const c = ih.cursor; return { picture: !!c.isInPictureObjectSelection?.(), table: !!c.isInTableObjectSelection?.(), layers: out }; })()`);
const setPanel = (on) => ev(`(async () => { const shown = !!D.querySelector('.claude-memo-panel'); if (shown !== ${on}) D.getElementById('tb-claude-memo').click(); await wait(900); return !!D.querySelector('.claude-memo-panel'); })()`);
const all = await ev(`(() => { const d = ih.wasm.doc; const o = []; for (let p = 0; p < d.pageCount(); p++) for (const c of JSON.parse(d.getPageControlLayout(p)).controls) o.push({ page: p, type: c.type, x: c.x, y: c.y, w: c.w, h: c.h, depth: (c.stableIndex?.length ?? 3) / 3 }); return o; })()`);
const pic = all.find((c) => c.type === 'image');
for (const on of [true, false, true, false]) {
  const shown = await setPanel(on);
  // 초기화: Esc 두 번, 그리고 1쪽 본문 글을 눌러 커서를 놓는다
  await key('Escape', 'Escape', 27); await key('Escape', 'Escape', 27);
  const t = await screenOf(0, 300, 200, 200);
  await click(t.x, t.y);
  const before = await layers(0);
  const p = await screenOf(pic.page, pic.x + pic.w / 2, pic.y + pic.h / 2, pic.y + pic.h / 2);
  await click(p.x, p.y);
  const after = await layers(pic.page);
  console.log(`== ${shown ? '패널 열림' : '패널 닫힘'}: 누르기 전 그림 ${before.picture} 표 ${before.table} 층 ${JSON.stringify(Object.keys(before.layers))}`);
  console.log(`   누른 뒤 그림 ${after.picture} 표 ${after.table}`);
  for (const [name, kids] of Object.entries(after.layers)) console.log(`   ${name}: ${kids.join(' | ')}`);
}
console.log('그림 상자(쪽 좌표)', Math.round(pic.x), Math.round(pic.y), Math.round(pic.w) + 'x' + Math.round(pic.h));
ws.close();
