// 정답본 문서마다 에디터가 엔진에 등록할 글꼴 폭 표(font-metrics.mjs docFontMetrics)를 out/metrics/<id>.json 으로 뽑는다.
// 네이티브 채점(nativescore.py)이 같은 표를 등록해 wasm 채점(score.mjs)과 같은 조건에서 재게 한다.
//   node dump_metrics.mjs [--force]
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ED = 'C:/Users/hccga/.claude/skills/hwpx/editor/';
const m = await import(pathToFileURL(ED + 'studio-dist/node/rhwp.js').href);
m.initSync({ module: fs.readFileSync(ED + 'studio-dist/node/rhwp_bg.wasm') });
const { docFontMetrics } = await import(pathToFileURL(ED + 'font-metrics.mjs').href);

const src = path.join(HERE, '..', 'out', 'oracle');
const dst = path.join(HERE, '..', 'out', 'metrics');
fs.mkdirSync(dst, { recursive: true });
let n = 0;
for (const f of fs.readdirSync(src).filter((x) => x.endsWith('.hwpx'))) {
  const out = path.join(dst, f.replace(/\.hwpx$/, '.json'));
  if (!process.argv.includes('--force') && fs.existsSync(out)) continue;
  fs.writeFileSync(out, JSON.stringify(docFontMetrics(fs.readFileSync(path.join(src, f)), m).metrics));
  n++;
}
console.log(`폭 표 ${n}개 새로 뽑음 → ${dst}`);
