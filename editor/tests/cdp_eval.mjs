// 앱 창(WebView2, --remote-debugging-port)의 페이지에서 JS 식 하나를 평가한다. 시험, 진단용.
//   node editor/tests/cdp_eval.mjs <포트> "<식>"      — studio iframe 은 S 로 부른다(contentWindow)
const [port, expr] = process.argv.slice(2);
const targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
const page = targets.find((t) => t.type === 'page');
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener('open', r));
const wrapped = `(async () => { const S = document.querySelector('iframe').contentWindow; return JSON.stringify(await (${expr})); })()`;
ws.send(JSON.stringify({ id: 1, method: 'Runtime.evaluate', params: { expression: wrapped, awaitPromise: true } }));
ws.addEventListener('message', (m) => {
  const msg = JSON.parse(m.data);
  if (msg.id !== 1) return;
  console.log(msg.result?.result?.value ?? JSON.stringify(msg.result?.exceptionDetails ?? msg));
  ws.close();
});
