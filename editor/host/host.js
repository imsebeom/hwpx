// 호스트 페이지: rhwp-studio 를 띄우고 브리지 서버와 명령, 스냅샷을 주고받는다.
import { createStudio } from '/sdk/index.js';

const $ = (id) => document.getElementById(id);
const setStatus = (text, cls = '') => { $('status').textContent = text; $('dot').className = cls; };
const log = (text) => { $('log').textContent = `${new Date().toLocaleTimeString()} ${text}`; };

const studio = await createStudio('#editor', {
  studioUrl: `${location.origin}/studio/`,
  plugins: ['hwpctrl', 'claude'],
});

const postLog = (ev, data = {}) => fetch('/api/log', { method: 'POST', body: JSON.stringify({ ev, ...data }) }).catch(() => {});

/**
 * 에디터 화면의 저장과 열기를 작업 기록에 남긴다. 스튜디오는 저장 이벤트를 내보내지 않고 File System Access API
 * (showSaveFilePicker → createWritable)로 파일을 쓰므로, iframe(같은 출처) 안의 그 함수들을 감싼다.
 * 브라우저는 전체 경로를 알려 주지 않아 파일 이름만 남는다.
 */
function watchFileAccess() {
  const w = $('editor').querySelector('iframe')?.contentWindow;
  const proto = w?.FileSystemFileHandle?.prototype;
  if (!proto || proto.__claudeLogged) return;
  proto.__claudeLogged = true;
  const create = proto.createWritable;
  proto.createWritable = async function (...args) {
    const handle = this;
    const writable = await create.apply(this, args);
    let bytes = 0;
    const write = writable.write.bind(writable);
    writable.write = (data) => {
      const d = data?.type === 'write' ? data.data : data;
      bytes += d?.size ?? d?.byteLength ?? 0;
      return write(data);
    };
    const close = writable.close.bind(writable);
    writable.close = async () => {
      const r = await close();
      postLog('save', { by: 'user', name: handle.name, bytes, via: '에디터 화면' });
      log(`저장 기록: ${handle.name}`);
      return r;
    };
    return writable;
  };
  if (w.showOpenFilePicker) {
    const pick = w.showOpenFilePicker.bind(w);
    w.showOpenFilePicker = async (...args) => {
      const hs = await pick(...args);
      postLog('open-file', { by: 'user', names: hs.map((h) => h.name), via: '에디터 화면' });
      return hs;
    };
  }
}

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

const plugin = (method, ...args) => studio.plugins.invoke('claude', method, args);
const run = (ops) => plugin('run', ops);

async function docText() {
  const [text] = await run([{ m: 'GetTextFile', a: ['UNICODE', ''] }]);
  return String(text ?? '');
}

/** 머리말/꼬리말 문단별 모델 텍스트. 저장 단계 쪽 번호 보정(hwpx-zip.mjs)이 표식 위치를 찾는 데 쓴다. */
async function headerFooterTexts() {
  const [list] = await run([{ doc: 'getHeaderFooterList', a: [0, false, 0] }]);
  const out = [];
  for (const it of list?.items ?? []) {
    const [info] = await run([{ doc: 'getHeaderFooter', a: [it.sectionIdx, it.isHeader, it.applyTo] }]);
    const n = info?.paraCount ?? 0;
    const ops = Array.from({ length: n }, (_, i) => ({ doc: 'getHeaderFooterParaInfo', a: [it.sectionIdx, it.isHeader, it.applyTo, i] }));
    const paras = n ? (await run(ops)).map((r) => r?.text ?? '') : [];
    out.push({ section: it.sectionIdx, isHeader: it.isHeader, applyTo: it.applyTo, paras });
  }
  return out;
}

// 문서 변경 카운터(플러그인이 document-mutated 이벤트를 센다). 사용자 편집 감지에 쓴다.
const mutationKey = () => plugin('mutations');

async function cursor() {
  try { return await plugin('cursor'); } catch { return null; }
}

async function snapshot(source) {
  const key = await mutationKey();
  const bytes = await studio.exportHwpx();
  const body = {
    source,
    changeSeq: key,
    text: await docText(),
    model: await plugin('model'),          // 본문 문단 글과 셀 문단 글(좌표 diff 용)
    cursor: await cursor(),
    hwpxBase64: toBase64(bytes),
  };
  const r = await fetch('/api/snapshot', { method: 'POST', body: JSON.stringify(body) }).then((x) => x.json());
  lastKey = key;
  log(`${source === 'user' ? '사용자 수정' : source === 'claude' ? 'Claude 수정' : '열림'} 기록 (${r.diffLines ?? 0}곳 변경)`);
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
    return { ok: true, state: await studio.getDocumentState(), cursor: await cursor(), pageCount: await studio.pageCount() };
  },
  async outline(cmd) { return { ok: true, text: await plugin('outline', cmd.opts || {}) }; },
  async inspect(cmd) { return { ok: true, docType: await plugin('docType'), result: await plugin('inspect', cmd.docType) }; },
  async slots() { return { ok: true, result: await plugin('slots') }; },
  async tools() { return { ok: true, result: await plugin('tools') }; },
  async goto(cmd) { return { ok: true, result: await plugin('goto', cmd.ref) }; },
  async save() {
    const hfMarkers = await headerFooterTexts();
    return { ok: true, base64: toBase64(await studio.exportHwpx()), hfMarkers };
  },
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
      postLog('error', { by: 'claude', cmd: cmd.type, error: reply.error.slice(0, 300) });
    } finally {
      busy = false;
    }
    await fetch('/api/result', { method: 'POST', body: JSON.stringify({ id: cmd.id, ...reply }) }).catch(() => {});
  }
}

// 사용자 편집 감지: 변경 카운터가 바뀌고 1.5초 동안 더 안 바뀌면 한 번 기록한다.
let pendingKey = null;
setInterval(async () => {
  if (busy || lastKey === null) return;
  try {
    const key = await mutationKey();
    if (key === lastKey) { pendingKey = null; return; }
    if (key !== pendingKey) { pendingKey = key; return; }   // 아직 입력 중
    pendingKey = null;
    await snapshot('user');
  } catch { /* 문서 교체 중이면 다음 주기에 */ }
}, 1500);

setStatus('Claude 연결 대기', '');
watchFileAccess();
await openFromServer();
pollLoop();
