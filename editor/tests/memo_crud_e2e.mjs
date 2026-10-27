// 메모 CRUD 끝에서 끝 시험: 미리보기 모드로 띄운 에디터에 보이지 않는 크로미움으로 붙어
// cli memos add/edit/del 과 패널 「고치기」, 「지우기」, Ctrl+Z 를 차례로 해 보고 저장본을 다시 연다.
//   node editor/tests/memo_crud_e2e.mjs <메모 든 문서 사본.hwpx>   (문서 폴더에 새 판 <이름>_<날짜>_NN.hwpx 와 panel.png 가 생긴다)
// 창을 띄우지 않는다(HWPX_EDITOR_MODE=preview). studio 는 호스트 페이지의 `#editor iframe` 안에 있다.
// playwright-core 위치는 PLAYWRIGHT_CORE(기본 C:/dev/pwrun/node_modules/playwright-core — npm 으로 playwright-core 를 깐 폴더와 크로미움이 있으면 된다).
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const { chromium } = await import(pathToFileURL(path.join(process.env.PLAYWRIGHT_CORE || 'C:/dev/pwrun/node_modules/playwright-core', 'index.mjs')).href);
const HERE = path.dirname(fileURLToPath(import.meta.url));
const CLI = path.join(HERE, '..', 'cli.mjs');
const env = { ...process.env, HWPX_EDITOR_INSTANCE: 'memoe2e', HWPX_EDITOR_MODE: 'preview' };
const cli = (...a) => execFileSync(process.execPath, [CLI, ...a], { env, encoding: 'utf8', cwd: path.dirname(process.argv[2]) }).trim();
const list = () => JSON.parse(cli('memos', '--json'));
const check = (name, ok, extra = '') => { console.log(`${ok ? '통과' : '실패'} ${name}${extra ? ` — ${extra}` : ''}`); if (!ok) process.exitCode = 1; };

console.log(cli('start', process.argv[2]));
const url = cli('url').split(/\s+/).find((s) => s.startsWith('http'));
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1500, height: 1000 } });
await page.goto(url);
const f = page.frameLocator('#editor iframe');
await f.locator('.claude-memo-panel li').first().waitFor({ timeout: 60000 });

const m0 = list();
console.log(`메모 ${m0.length}개`);
const text0 = cli('text');

// ① cli add: 첫 문단 전체 + 낱말 하나에 건 메모
cli('memos', 'add', 'p0', 'Claude 가 단 메모\\n둘째 줄');
let m = list();
check('cli add', m.length === m0.length + 1 && m.some((x) => x.author === 'Claude' && x.text === 'Claude 가 단 메모\n둘째 줄'), `${m.length}개`);
// ② cli edit
const ni = m.findIndex((x) => x.author === 'Claude') + 1;
cli('memos', 'edit', String(ni), '고친 본문');
m = list();
check('cli edit', m[ni - 1].text === '고친 본문' && m.length === m0.length + 1);
// ③ cli del
cli('memos', 'del', String(ni));
m = list();
check('cli del', m.length === m0.length && cli('text') === text0, `${m.length}개, 글 같음 ${cli('text') === text0}`);

// ④ 패널 「지우기」 → Ctrl+Z
await page.waitForTimeout(800);
const before = await f.locator('.claude-memo-panel li').count();
await f.locator('.claude-memo-panel li').first().hover();
await f.locator('.claude-memo-panel li .acts button', { hasText: '지우기' }).first().click();
await page.waitForTimeout(800);
const afterDel = await f.locator('.claude-memo-panel li').count();
check('패널 지우기', afterDel === before - 1 && list().length === m0.length - 1, `${before} → ${afterDel}`);
cli('undo');
await page.waitForTimeout(800);
check('되돌리기', list().length === m0.length && JSON.stringify(list().map((x) => x.text)) === JSON.stringify(m0.map((x) => x.text)));

// ⑤ 패널 「고치기」 → 친 뒤 Ctrl+Enter
await f.locator('.claude-memo-panel li').nth(1).hover();
await f.locator('.claude-memo-panel li').nth(1).locator('.acts button', { hasText: '고치기' }).click();
const box = f.locator('.claude-memo-panel textarea');
await box.fill('패널에서 고침\n두 줄');
await box.press('Control+Enter');
await page.waitForTimeout(800);
m = list();
check('패널 고치기', m[1].text === '패널에서 고침\n두 줄' && m[1].author === m0[1].author && m[1].anchor === m0[1].anchor, JSON.stringify(m[1].text));
const shot = path.join(path.dirname(process.argv[2]), 'panel.png');
await page.screenshot({ path: shot });

// ⑥ 저장 → 저장본을 엔진으로 다시 열어 메모 확인
const saved = cli('save');
console.log(saved);
const file = saved.match(/[A-Z]:[^\s]+\.hwpx|\S+\.hwpx/g)?.pop();
await browser.close();
cli('stop');
if (file && fs.existsSync(file)) {
  const dir = path.join(HERE, '..', 'studio-dist', 'node');
  const w = await import(pathToFileURL(path.join(dir, 'rhwp.js')).href);
  w.initSync({ module: fs.readFileSync(path.join(dir, 'rhwp_bg.wasm')) });
  const doc = new w.HwpDocument(new Uint8Array(fs.readFileSync(file)));
  const re = JSON.parse(doc.getMemoList());
  check('저장본 다시 열기', re.length === m0.length && re.some((x) => x.text === '패널에서 고침\n두 줄'), `${re.length}개`);
} else check('저장본 찾기', false, saved);
