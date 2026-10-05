// 글꼴 이름들의 폭 표를 JSON 으로 낸다: node fm_dump.mjs <out.json> <이름...>
import fs from 'node:fs';
const { metricsFor } = await import('file:///C:/Users/hccga/.claude/skills/hwpx/editor/font-metrics.mjs');
const [out, ...names] = process.argv.slice(2);
const res = {};
for (const n of names) res[n] = metricsFor(n);
fs.writeFileSync(out, JSON.stringify(res));
for (const n of names) console.log(n, res[n].map((f) => `${f.bold ? 'B' : 'R'}:${f.file.split(/[\/]/).pop()}`).join(' ') || '못 찾음');
