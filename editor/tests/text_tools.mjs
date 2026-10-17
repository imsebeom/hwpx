// 글 도구 회귀 시험: format_text(글꼴, 장평, 자간), regex_replace(묶음, 색 조건, 기대 개수), table_caption.
//   node editor/tests/text_tools.mjs [--out <폴더>]
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const dir = path.join(HERE, '..', 'studio-dist', 'node');
const m = await import(pathToFileURL(path.join(dir, 'rhwp.js')).href);
m.initSync({ module: fs.readFileSync(path.join(dir, 'rhwp_bg.wasm')) });
const { runTool } = await import(pathToFileURL(path.join(HERE, '..', 'plugin', 'lib', 'doc-tools.js')).href);
const { readZip } = await import(pathToFileURL(path.join(HERE, '..', 'hwpx-zip.mjs')).href);
const FIX = path.join(HERE, '..', '..', 'tests', 'fixtures');
const outDir = process.argv.includes('--out') ? process.argv[process.argv.indexOf('--out') + 1] : null;
const open = () => new m.HwpDocument(fs.readFileSync(path.join(FIX, 'short_table_md2hwpx.hwpx')));
const part = (doc, name) => readZip(Buffer.from(doc.exportHwpx()), (n) => n === name)[0].data.toString('utf8');
let failed = 0;
const check = (label, ok, info = '') => { failed += !ok; console.log(`${ok ? 'PASS' : 'FAIL'} ${label}${info ? ` — ${info}` : ''}`); };

// format_text: 글꼴, 장평, 자간
{
  const doc = open();
  const r = runTool(doc, 'format_text', { at: 'T1r1c1', font: '맑은 고딕', width_percent: 90, spacing_percent: -5 }).result;
  check('format_text 적용', r.ok, JSON.stringify(r));
  const h = part(doc, 'Contents/header.xml');
  check('글꼴 「맑은 고딕」 등록', /face="맑은 고딕"/.test(h));
  check('장평 90, 자간 -5 저장', /<hh:ratio hangul="90"/.test(h) && /<hh:spacing hangul="-5"/.test(h));
  check('범위 밖 장평 거부', !runTool(doc, 'format_text', { at: 'T1r1c1', width_percent: 300 }).result.ok);
  if (outDir) fs.writeFileSync(path.join(outDir, 'format_text.hwpx'), Buffer.from(doc.exportHwpx()));
}

// regex_replace
{
  const doc = open();
  let r = runTool(doc, 'regex_replace', { pattern: '끝(\\d+)', replace: '마감$1' }).result;
  check('묶음 치환(표 칸 포함)', r.ok && r.count === 3 && /마감00/.test(r.sample[0]), JSON.stringify(r));
  r = runTool(doc, 'regex_replace', { pattern: 'R0\\d', replace: 'X', expected_count: 1 }).result;
  check('기대 개수 다르면 바꾸지 않음', !r.ok && /3곳/.test(r.error), r.error);
  runTool(doc, 'format_text', { at: 'T1r1c1', text: '짧음', color: '#ff0000' });
  r = runTool(doc, 'regex_replace', { pattern: '짧음', replace: '김', color: '#ff0000' }).result;
  check('색 조건: 빨간 글자만', r.ok && r.count === 1, JSON.stringify(r));
  check('잘못된 정규식 거부', !runTool(doc, 'regex_replace', { pattern: '(', replace: '' }).result.ok);
}

// table_caption: 한/글이 만드는 구조 <hp:t>표 </hp:t>{번호}<hp:t> 제목</hp:t>, 기본 아래
{
  const doc = open();
  let r = runTool(doc, 'table_caption', { table: 'T1', text: '학년별 일정' }).result;
  check('캡션 달기', r.ok && r.position === 'bottom', JSON.stringify(r));
  let cap = part(doc, 'Contents/section0.xml').match(/<hp:caption\b[\s\S]*?<\/hp:caption>/)?.[0] || '';
  const seq = (c) => [...c.matchAll(/<hp:t>([^<]*)<\/hp:t>|<hp:autoNum\b/g)].map((y) => (y[0].startsWith('<hp:autoNum') ? '{번호}' : y[1])).join('');
  check('한/글과 같은 구조', /side="BOTTOM"/.test(cap) && seq(cap) === '표 {번호} 학년별 일정', seq(cap));
  r = runTool(doc, 'table_caption', { table: 'T1', text: '월별 일정', position: 'top' }).result;
  cap = part(doc, 'Contents/section0.xml').match(/<hp:caption\b[\s\S]*?<\/hp:caption>/)?.[0] || '';
  check('제목 바꾸기, 위로', r.ok && /side="TOP"/.test(cap) && seq(cap) === '표 {번호} 월별 일정', seq(cap));
  if (outDir) fs.writeFileSync(path.join(outDir, 'caption.hwpx'), Buffer.from(doc.exportHwpx()));
}

if (failed) process.exit(1);
console.log('모두 통과');
