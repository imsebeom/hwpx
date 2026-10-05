// 메모 패널 동작 점검: node memo_e2e.mjs  (hold.py 로 CDP 9333 이 열려 있어야 한다)
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
  const wrapped = `(async () => { const S = document.querySelector('iframe').contentWindow; const D = S.document; const wait = (ms) => new Promise((r) => setTimeout(r, ms)); return JSON.stringify(await (${expr})); })()`;
  const r = await call('Runtime.evaluate', { expression: wrapped, awaitPromise: true });
  return r.result?.result?.value ? JSON.parse(r.result.result.value) : r.result?.exceptionDetails ?? r;
};
const snap = `({ panel: !!D.querySelector('.claude-memo-panel'), cards: D.querySelectorAll('.claude-memo-panel li').length, hl: D.querySelectorAll('.claude-memo-hl').length, pins: D.querySelectorAll('.claude-memo-pin').length, btn: D.querySelector('#tb-claude-memo .tb-label')?.textContent, margin: D.getElementById('editor-area').style.marginRight, hidden: S.localStorage.getItem('claude-memo-hidden') })`;
console.log('처음', await ev(snap));
// 번호 표 5의 화면 좌표(확대 전)
const pin = `(() => { const p = D.querySelector('.claude-memo-pin[data-i="4"]'); const r = p.getBoundingClientRect(); return { x: Math.round(r.left), y: Math.round(r.top), top: p.style.top, left: p.style.left }; })()`;
console.log('번호 표 5', await ev(pin));
// 확대 150%
console.log('확대', await ev(`(S.__claudeIH().viewportManager.setZoom(1.5), wait(700).then(() => ({ zoom: S.__claudeIH().viewportManager.getZoom(), pin: ${pin} })))`));
console.log('되돌림', await ev(`(S.__claudeIH().viewportManager.setZoom(1.0), wait(700).then(() => ({ zoom: S.__claudeIH().viewportManager.getZoom(), pin: ${pin} })))`));
// 번호 표 누르기 → 패널 강조
console.log('번호 표 누름', await ev(`(D.querySelector('.claude-memo-pin[data-i="7"]').click(), wait(200).then(() => [...D.querySelectorAll('.claude-memo-panel li.on')].map((e) => e.dataset.i)))`));
// 숨기기 → 다시 열기
console.log('숨김', await ev(`(D.getElementById('tb-claude-memo').click(), wait(500).then(() => ${snap}))`));
console.log('다시 엶', await ev(`(D.getElementById('tb-claude-memo').click(), wait(700).then(() => ${snap}))`));
ws.close();
