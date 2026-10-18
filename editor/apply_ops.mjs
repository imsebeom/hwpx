#!/usr/bin/env node
/**
 * 화면 없이 에디터 편집 도구를 문서 파일에 적용한다 — 빌더(스크립트) 쪽에서 에디터 도구 36종을 그대로 쓰는 다리.
 *
 *   node apply_ops.mjs <문서.hwpx|.hwp> <작업.json | -> -o <결과.hwpx> [--keep-going]
 *   node apply_ops.mjs --tools        도구 목록(이름과 설명)
 *
 * 작업 JSON 은 에디터 `cli.mjs run` 과 같다: [{ "tool": "page_setup", "args": {...} }, { "doc": "메서드", "a": [...] }, ...].
 * 도구 정의는 editor/plugin/lib/doc-tools.js 의 TOOLS 와 lib/run-ops.js 의 EXTRA_TOOLS(`--tools` 로 본다).
 * HwpCtrl 메서드({ m }, { run })와 그림({ image })은 화면이 있는 에디터에서만 된다 — 그림은 빌더의 insert_image_at 을 쓴다.
 * 한 작업이라도 실패하면 결과를 쓰지 않는다(에디터의 「배치 하나 = 되돌리기 한 번」과 같다). --keep-going 이면 실패를 건너뛴다.
 * 문서를 열기 전에 문서가 쓰는 글꼴의 폭 표를 등록한다(에디터와 같은 줄 나눔).
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const die = (msg) => { console.error(msg); process.exit(2); };

const { TOOLS } = await import(pathToFileURL(path.join(HERE, 'plugin', 'lib', 'doc-tools.js')).href);
const { EXTRA_TOOLS, stepCore } = await import(pathToFileURL(path.join(HERE, 'plugin', 'lib', 'run-ops.js')).href);

if (args.includes('--tools')) {
  for (const t of [...TOOLS, ...EXTRA_TOOLS]) console.log(`${t.name}\t${t.description.split(/(?<=[.다])\s/)[0]}`);
  process.exit(0);
}

const outAt = args.indexOf('-o');
const output = outAt >= 0 ? args[outAt + 1] : null;
const positional = args.filter((a, i) => !a.startsWith('--') && a !== '-o' && i !== outAt + 1);
const [input, opsArg] = positional;
if (!input || !opsArg || !output) die('사용법: node apply_ops.mjs <문서.hwpx> <작업.json | -> -o <결과.hwpx> [--keep-going]');
if (!fs.existsSync(input)) die(`문서가 없다: ${input}`);
const keepGoing = args.includes('--keep-going');

const opsText = opsArg === '-' ? fs.readFileSync(0, 'utf8') : fs.readFileSync(opsArg, 'utf8');
// KS X 6101 §5.3: 본문은 NFC(cli.mjs run 과 같다)
const parsed = JSON.parse(opsText, (k, v) => (typeof v === 'string' ? v.normalize('NFC') : v));
const ops = Array.isArray(parsed) ? parsed : [parsed];

const engineDir = process.env.RHWP_ENGINE || path.join(HERE, 'studio-dist', 'node');
if (!fs.existsSync(path.join(engineDir, 'rhwp.js'))) die(`엔진이 없다: ${engineDir} — 먼저 node setup.mjs`);
const mod = await import(pathToFileURL(path.join(engineDir, 'rhwp.js')).href);
mod.initSync({ module: fs.readFileSync(path.join(engineDir, 'rhwp_bg.wasm')) });
const bytes = fs.readFileSync(input);
if (/\.hwpx$/i.test(input)) {
  const { docFontMetrics, registerInto } = await import(pathToFileURL(path.join(HERE, 'font-metrics.mjs')).href);
  registerInto(mod, docFontMetrics(bytes, mod).metrics);
}
const doc = new mod.HwpDocument(bytes);

const results = [];
let failed = 0;
for (const [i, op] of ops.entries()) {
  try {
    if (!op.tool && !op.doc) throw new Error(op.m || op.run || op.image
      ? 'HwpCtrl({ m }, { run })과 그림({ image })은 화면이 있는 에디터(cli.mjs run, image)에서만 된다'
      : 'op 에 tool 이나 doc 이 있어야 한다');
    results.push({ i, ok: true, result: stepCore(doc, op) });
  } catch (e) {
    failed++;
    results.push({ i, ok: false, op: JSON.stringify(op).slice(0, 200), error: String(e?.message ?? e) });
    if (!keepGoing) break;
  }
}

if (failed && !keepGoing) {
  console.log(JSON.stringify({ ok: false, written: false, pages: doc.pageCount(), results }, null, 1));
  process.exit(1);
}
const out = doc.exportHwpx ? doc.exportHwpx() : null;
if (!out) die('이 엔진은 HWPX 로 내보내지 못한다');
fs.mkdirSync(path.dirname(path.resolve(output)), { recursive: true });
fs.writeFileSync(output, Buffer.from(out));
console.log(JSON.stringify({ ok: failed === 0, written: output, pages: doc.pageCount(), results }, null, 1));
process.exit(failed ? 1 : 0);
