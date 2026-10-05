// 대조 문서에서 엔진에 폭 표가 없는 글꼴(corpus_faces_metric.tsv 의 0)을 파일에서 읽어 등록용 JSON 을 만든다
import fs from 'node:fs';
const { metricsFor } = await import('file:///C:/Users/hccga/.claude/skills/hwpx/editor/font-metrics.mjs');
const names = fs.readFileSync('corpus_faces_metric.tsv', 'utf8').split(/\r?\n/).filter((l) => l.startsWith('0')).map((l) => l.split('\t')[1].trim());
const out = [];
const read = [], missing = [];
for (const n of names) {
  const faces = metricsFor(n);
  if (!faces.length) { missing.push(n); continue; }
  read.push(n);
  out.push(...faces.map(({ file, ...m }) => m));
}
fs.writeFileSync('rt_metrics.json', JSON.stringify(out));
console.log('표 없는 글꼴', names.length, '읽음', read.length, '얼굴', out.length, '못 찾음', missing.length, 'JSON', fs.statSync('rt_metrics.json').size);
console.log('못 찾은 것 일부:', missing.slice(0, 30).join(', '));
