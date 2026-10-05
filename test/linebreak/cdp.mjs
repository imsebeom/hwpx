// node cdp.mjs eval "<식>"   — studio iframe 은 S
// node cdp.mjs key ctrl+a      — 숨은 입력칸에 키 보내기(CDP Input)
// node cdp.mjs shot out.png
const [cmd, arg] = process.argv.slice(2);
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
if (cmd === 'eval') {
  const wrapped = `(async () => { const S = document.querySelector('iframe').contentWindow; return JSON.stringify(await (${arg})); })()`;
  const r = await call('Runtime.evaluate', { expression: wrapped, awaitPromise: true });
  console.log(r.result?.result?.value ?? JSON.stringify(r.result?.exceptionDetails ?? r));
} else if (cmd === 'key') {
  const [mod, k] = arg.split('+');
  const modifiers = mod === 'ctrl' ? 2 : 0;
  const code = 'Key' + k.toUpperCase();
  await call('Input.dispatchKeyEvent', { type: 'rawKeyDown', key: 'Control', code: 'ControlLeft', windowsVirtualKeyCode: 17, modifiers });
  await call('Input.dispatchKeyEvent', { type: 'rawKeyDown', key: k, code, windowsVirtualKeyCode: k.toUpperCase().charCodeAt(0), modifiers });
  await call('Input.dispatchKeyEvent', { type: 'keyUp', key: k, code, windowsVirtualKeyCode: k.toUpperCase().charCodeAt(0), modifiers });
  await call('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Control', code: 'ControlLeft', windowsVirtualKeyCode: 17, modifiers: 0 });
  console.log('sent', arg);
} else if (cmd === 'press') {
  // node cdp.mjs press Home|End|ArrowLeft|ArrowRight|Backspace [shift]
  const VKS = { Home: 36, End: 35, ArrowLeft: 37, ArrowRight: 39, ArrowUp: 38, ArrowDown: 40, Backspace: 8, Delete: 46 };
  const modifiers = process.argv[4] === 'shift' ? 8 : 0;
  await call('Input.dispatchKeyEvent', { type: 'rawKeyDown', key: arg, code: arg, windowsVirtualKeyCode: VKS[arg], modifiers });
  await call('Input.dispatchKeyEvent', { type: 'keyUp', key: arg, code: arg, windowsVirtualKeyCode: VKS[arg], modifiers });
  console.log('pressed', arg);
} else if (cmd === 'click') {
  const [x, y] = arg.split(',').map(Number);
  for (const type of ['mousePressed', 'mouseReleased']) await call('Input.dispatchMouseEvent', { type, x, y, button: 'left', clickCount: 1 });
  console.log('clicked', arg);
} else if (cmd === 'shot') {
  const r = await call('Page.captureScreenshot', { format: 'png' });
  (await import('node:fs')).writeFileSync(arg, Buffer.from(r.result.data, 'base64'));
  console.log('saved', arg);
}
ws.close();
