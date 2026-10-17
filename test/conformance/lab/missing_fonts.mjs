// 정답본 코퍼스에서 엔진 내장 표도 글꼴 파일도 없는 글꼴(한컴 내장 HFT 등)이 몇 문서에서 쓰이는지 센다.
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
const ED = 'C:/Users/hccga/.claude/skills/hwpx/editor/';
const m = await import(pathToFileURL(ED + 'studio-dist/node/rhwp.js').href);
m.initSync({ module: fs.readFileSync(ED + 'studio-dist/node/rhwp_bg.wasm') });
const { docFontMetrics } = await import(pathToFileURL(ED + 'font-metrics.mjs').href);
const dir = 'out/oracle';
const cnt = new Map();
for (const f of fs.readdirSync(dir).filter((x) => x.endsWith('.hwpx'))) {
  const r = docFontMetrics(fs.readFileSync(path.join(dir, f)), m);
  for (const n of r.missing) cnt.set(n, (cnt.get(n) || 0) + 1);
}
console.log([...cnt].sort((a, b) => b[1] - a[1]).slice(0, 30).map(([n, c]) => `${n}:${c}`).join('  '));
