// 빌더 쪽 다리(apply_ops.mjs) 시험: 에디터 도구 대표 10종을 화면 없이 파일에 적용하고, 결과 파일을 다시 열어 확인한다.
//   node editor/tests/apply_ops.mjs [--out <폴더>]
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const EDITOR = path.join(HERE, '..');
const FIX = path.join(EDITOR, '..', 'tests', 'fixtures');
const outDir = process.argv.includes('--out') ? process.argv[process.argv.indexOf('--out') + 1] : fs.mkdtempSync(path.join(os.tmpdir(), 'apply-ops-'));
fs.mkdirSync(outDir, { recursive: true });
const dir = path.join(EDITOR, 'studio-dist', 'node');
const m = await import(pathToFileURL(path.join(dir, 'rhwp.js')).href);
m.initSync({ module: fs.readFileSync(path.join(dir, 'rhwp_bg.wasm')) });
const { readZip } = await import(pathToFileURL(path.join(EDITOR, 'hwpx-zip.mjs')).href);
let failed = 0;
const check = (label, ok, info = '') => { failed += !ok; console.log(`${ok ? 'PASS' : 'FAIL'} ${label}${info ? ` — ${info}` : ''}`); };
const run = (input, ops, output, extra = []) => {
  const opsFile = path.join(outDir, `ops_${path.basename(output)}.json`);
  fs.writeFileSync(opsFile, JSON.stringify(ops));
  const r = spawnSync(process.execPath, [path.join(EDITOR, 'apply_ops.mjs'), input, opsFile, '-o', output, ...extra], { encoding: 'utf8' });
  return { status: r.status, json: (() => { try { return JSON.parse(r.stdout); } catch { return { raw: r.stdout + r.stderr }; } })() };
};
const part = (file, name) => readZip(fs.readFileSync(file), (n) => n === name)[0].data.toString('utf8');

const src = path.join(FIX, 'short_table_md2hwpx.hwpx');
const srcSec = part(src, 'Contents/section0.xml');
const out = path.join(outDir, 'applied.hwpx');
const ops = [
  { tool: 'regex_replace', args: { pattern: 'R0(\\d)', replace: '행$1', expected_count: 3 } },
  { tool: 'format_text', args: { at: 'p3', bold: true, size_pt: 14 } },
  { tool: 'format_paragraph', args: { at: 'p5', align: 'center' } },
  { tool: 'page_setup', args: { orientation: 'landscape' } },
  { tool: 'set_header_footer', args: { which: 'footer', text: '- {쪽} -', align: 'center' } },
  { tool: 'add_footnote', args: { para: 3, text: '각주 시험' } },
  { tool: 'table_caption', args: { table: 'T1', text: '시험 표' } },
  { tool: 'set_cell', args: { table: 'T1', row: 1, col: 1, text: '10' } },
  { tool: 'set_cell', args: { table: 'T1', row: 2, col: 1, text: '20' } },
  { tool: 'table_formula', args: { table: 'T1', row: 3, col: 1, formula: '=B2+B3' } },
  { tool: 'merge_cells', args: { table: 'T1', from_row: 1, from_col: 0, to_row: 2, to_col: 0 } },
  { tool: 'split_cell', args: { table: 'T1', row: 1, col: 0 } },
  { tool: 'insert_table_column', args: { table: 'T1', col: 1, right: true } },
];
const r = run(src, ops, out);
check('작업 13건 모두 성공하고 파일을 씀', r.status === 0 && r.json.ok && fs.existsSync(out), JSON.stringify(r.json.results?.filter((x) => !x.ok) ?? r.json).slice(0, 300));
if (fs.existsSync(out)) {
  const sec = part(out, 'Contents/section0.xml');
  const head = part(out, 'Contents/header.xml');
  const doc = new m.HwpDocument(fs.readFileSync(out));
  check('다시 열림', doc.pageCount() >= 1);
  check('regex_replace: 「행0~2」', ['행0', '행1', '행2'].every((t) => sec.includes(t)) && !sec.includes('R01'));
  check('format_text: 14pt 진하게 글자 모양', /<hh:charPr id="\d+" height="1400"[^>]*>[\s\S]*?<hh:bold\/>/.test(head));
  check('format_paragraph: 가운데 정렬 문단 모양', /<hh:align horizontal="CENTER"/.test(head));
  const dims = (x) => { const p = /<hp:pagePr [^>]*width="(\d+)" height="(\d+)"/.exec(x); return p ? [Number(p[1]), Number(p[2])] : null; };
  const [w0, h0] = dims(srcSec) ?? [0, 0];
  const [w1, h1] = dims(sec) ?? [0, 0];
  check('page_setup: 가로(폭 > 높이)', (w1 > h1) || (sec.includes('landscape="NARROWLY"') && !srcSec.includes('landscape="NARROWLY"')), `전 ${w0}x${h0} 후 ${w1}x${h1}`);
  check('set_header_footer: 꼬리말과 쪽 번호', /<hp:footer\b/.test(sec) && /<hp:autoNum[^>]*numType="PAGE"|<hp:pageNum\b/.test(sec));
  check('add_footnote: 각주', /<hp:footNote\b/.test(sec) && sec.includes('각주 시험'));
  check('table_caption: 캡션', /<hp:caption\b/.test(sec) && sec.includes('시험 표'));
  check('table_formula: B4 = 30', /<hp:t>30<\/hp:t>/.test(sec));
  check('merge_cells 뒤 split_cell: 병합 없음', !/rowSpan="2"/.test(sec));
  check('insert_table_column: 3열', /colCnt="3"/.test(sec));
}

// 실패한 작업이 있으면 파일을 쓰지 않는다
const bad = path.join(outDir, 'bad.hwpx');
const rb = run(src, [{ tool: 'format_text', args: { at: 'p3', bold: true } }, { tool: 'set_cell', args: { table: 'T9', row: 0, col: 0, text: 'x' } }], bad);
check('실패하면 쓰지 않음', rb.status === 1 && rb.json.written === false && !fs.existsSync(bad));
const rk = run(src, [{ tool: 'set_cell', args: { table: 'T9', row: 0, col: 0, text: 'x' } }, { tool: 'format_text', args: { at: 'p3', italic: true } }], bad, ['--keep-going']);
check('--keep-going 이면 실패를 건너뛰고 씀', rk.status === 1 && fs.existsSync(bad) && rk.json.results?.[1]?.ok === true);
const rm = run(src, [{ m: 'PutFieldText', a: ['x', 'y'] }], path.join(outDir, 'm.hwpx'));
check('HwpCtrl 작업은 화면 에디터 안내', rm.status === 1 && /화면이 있는 에디터/.test(JSON.stringify(rm.json)));

console.log(failed ? `실패 ${failed}건` : '모두 통과');
process.exit(failed ? 1 : 0);
