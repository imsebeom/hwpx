// 호스트 페이지: rhwp-studio 를 띄우고 브리지 서버와 명령, 스냅샷을 주고받는다.
import { createStudio } from '/sdk/index.js';

const $ = (id) => document.getElementById(id);
const setStatus = (text, cls = '') => { $('status').textContent = text; $('dot').className = cls; };
const log = (text) => { $('log').textContent = `${new Date().toLocaleTimeString()} ${text}`; };

const studio = await createStudio('#editor', {
  studioUrl: `${location.origin}/studio/`,
  plugins: ['hwpctrl', 'claude'],
});

let busy = false;          // Claude 명령 실행 중에는 사용자 변경 감지를 멈춘다
let lastKey = null;        // 마지막으로 기록한 문서 상태

function toBase64(bytes) {
  let s = '';
  for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
  return btoa(s);
}
function fromBase64(b64) {
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

const run = (ops) => studio.plugins.invoke('claude', 'run', [ops]);

async function docText() {
  const [text] = await run([{ m: 'GetTextFile', a: ['UNICODE', ''] }]);
  return String(text ?? '');
}

async function stateKey() {
  const st = await studio.getDocumentState();
  return { st, key: `${st.changeSeq}:${st.documentSha256}` };
}

async function selection() {
  try {
    const c = await studio.getSelectionContext();
    return c.target ? { section: c.target.section, paragraph: c.target.paragraph, collapsed: c.collapsed, page: c.page } : { page: c.page, collapsed: c.collapsed };
  } catch { return null; }
}

async function snapshot(source) {
  const { st, key } = await stateKey();
  const bytes = await studio.exportHwpx();
  const body = { source, changeSeq: st.changeSeq, text: await docText(), selection: await selection(), hwpxBase64: toBase64(bytes) };
  const r = await fetch('/api/snapshot', { method: 'POST', body: JSON.stringify(body) }).then((x) => x.json());
  lastKey = key;
  log(`${source === 'user' ? '사용자 수정' : source === 'claude' ? 'Claude 수정' : '열림'} 기록 (${r.diffLines ?? 0}줄 변경)`);
}

async function openFromServer() {
  const r = await fetch('/api/doc').then((x) => x.json());
  if (!r.ok) { setStatus('열 문서 없음', 'err'); return { ok: false, error: '세션에 문서가 없다' }; }
  const res = await studio.loadFile(fromBase64(r.base64), r.fileName, { skipUnsavedGuard: true });
  $('doc').textContent = r.fileName;
  document.title = `${r.fileName} · Claude 연결`;
  await snapshot('open');
  return { ok: true, pageCount: res.pageCount };
}

const handlers = {
  async open() { return openFromServer(); },
  async run(cmd) {
    const result = await run(cmd.ops);
    await snapshot('claude');
    return { ok: true, result };
  },
  async text() { return { ok: true, text: await docText() }; },
  async state() {
    const { st } = await stateKey();
    return { ok: true, state: st, selection: await selection(), pageCount: await studio.pageCount() };
  },
  async save() { return { ok: true, base64: toBase64(await studio.exportHwpx()) }; },
  async saved(cmd) { return { ok: true, ...(await studio.notifySaved(cmd.fileName)) }; },
  async undo() { const r = await studio.commands.execute('edit:undo'); await snapshot('claude'); return { ok: true, result: r }; },
  async svg(cmd) { return { ok: true, svg: await studio.getPageSvg(cmd.page ?? 0) }; },
};

async function pollLoop() {
  for (;;) {
    let cmd;
    try {
      cmd = await fetch('/api/poll').then((x) => x.json());
      setStatus('Claude 연결됨', 'ok');
    } catch {
      setStatus('브리지 서버 끊김', 'err');
      await new Promise((r) => setTimeout(r, 2000));
      continue;
    }
    if (!cmd.id) continue;
    busy = true;
    let reply;
    try {
      const h = handlers[cmd.type];
      reply = h ? await h(cmd) : { ok: false, error: `모르는 명령: ${cmd.type}` };
      if (cmd.type === 'run') log(`Claude 명령 ${cmd.ops.length}건 적용`);
    } catch (e) {
      reply = { ok: false, error: String(e?.message || e), code: e?.code };
      log(`명령 실패: ${reply.error}`);
    } finally {
      busy = false;
    }
    await fetch('/api/result', { method: 'POST', body: JSON.stringify({ id: cmd.id, ...reply }) }).catch(() => {});
  }
}

// 사용자 편집 감지: 문서 상태가 바뀌고 1.5초 동안 더 안 바뀌면 한 번 기록한다.
let pendingKey = null;
setInterval(async () => {
  if (busy || lastKey === null) return;
  try {
    const { key } = await stateKey();
    if (key === lastKey) { pendingKey = null; return; }
    if (key !== pendingKey) { pendingKey = key; return; }   // 아직 입력 중
    pendingKey = null;
    await snapshot('user');
  } catch { /* 문서 교체 중이면 다음 주기에 */ }
}, 1500);

setStatus('Claude 연결 대기', '');
await openFromServer();
pollLoop();
