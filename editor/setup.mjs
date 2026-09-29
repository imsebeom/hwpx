#!/usr/bin/env node
/**
 * rhwp-studio 를 claude 플러그인을 넣어 빌드하고 studio-dist/, sdk/ 를 만든다.
 * Rust(~/.cargo 의 cargo, wasm-pack)가 있으면 patches/ 를 적용해 WASM 을 직접 빌드하고, 없으면 같은 버전의
 * npm @rhwp/core prebuilt 를 쓴다(이때 머리말/꼬리말 쪽 번호는 cli save 의 보정이 살린다).
 * 에디터 앱 창(app.py)은 파이썬 pywebview 가 필요하다: pip install pywebview
 *
 *   node setup.mjs            (이미 받은 소스가 있으면 재사용)
 *   node setup.mjs --clean    (.build 를 지우고 처음부터)
 *
 * rhwp 버전을 올릴 때는 RHWP_VERSION 만 바꾸고 --clean 으로 다시 돌린다.
 */
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const RHWP_VERSION = '0.8.6';
const HERE = path.dirname(fileURLToPath(import.meta.url));
const BUILD = path.join(HERE, '.build');
const RHWP = path.join(BUILD, 'rhwp');
const STUDIO = path.join(RHWP, 'rhwp-studio');

function exec(file, args, opts) {
  console.log(`$ ${[file, ...args].join(' ')}`);
  const r = spawnSync(file, args, { ...opts, encoding: 'utf8', maxBuffer: 256 * 1024 * 1024 });
  process.stdout.write((r.stdout || '') + (r.stderr || ''));
  if (r.error) throw r.error;
  if (r.status !== 0) throw new Error(`실패(${r.status}): ${file} ${args.join(' ')}`);
}
const sh = (command, cwd) => exec(command, [], { cwd, shell: true });

// Node 24.11 의 fs.rmSync/cpSync(recursive)는 한글 경로에서 node 를 통째로 죽인다(0xC0000409,
// 종료 코드 127, 메시지 없음). 이 폴더 경로에 한글이 있으므로 한 단계씩 도는 구현을 쓴다.
function rmrf(p) {
  if (!fs.existsSync(p)) return;
  if (fs.lstatSync(p).isDirectory()) {
    for (const f of fs.readdirSync(p)) rmrf(path.join(p, f));
    fs.rmdirSync(p);
  } else {
    try { fs.unlinkSync(p); } catch { fs.chmodSync(p, 0o666); fs.unlinkSync(p); }   // git pack 은 읽기 전용
  }
}
function copyDir(src, dst) {
  fs.mkdirSync(dst, { recursive: true });
  for (const f of fs.readdirSync(src)) {
    const s = path.join(src, f), d = path.join(dst, f);
    if (fs.statSync(s).isDirectory()) copyDir(s, d); else fs.copyFileSync(s, d);
  }
}

if (process.argv.includes('--clean')) rmrf(BUILD);
fs.mkdirSync(BUILD, { recursive: true });

// 1. 소스
if (!fs.existsSync(path.join(STUDIO, 'package.json'))) {
  sh(`git -c advice.detachedHead=false clone --depth 1 --branch v${RHWP_VERSION} https://github.com/edwardkim/rhwp.git rhwp`, BUILD);
}

// 2. WASM → ../pkg (studio 의 vite alias 가 여기를 본다)
//    Rust(cargo, wasm-pack)가 있으면 패치한 소스로 직접 빌드하고, 없으면 npm prebuilt 를 쓴다.
//    prebuilt 에서는 머리말/꼬리말 쪽 번호가 저장 시 빠지지만 cli.mjs save 의 보정(hwpx-zip.mjs)이 살린다.
const pkgDir = path.join(RHWP, 'pkg');
const cargoBin = path.join(os.homedir(), '.cargo', 'bin');
const hasRust = ['cargo', 'wasm-pack'].every((b) => fs.existsSync(path.join(cargoBin, `${b}${process.platform === 'win32' ? '.exe' : ''}`)));
// 패치 두 형태: anchor 앞에 insert 끼우기, 또는 find 를 replace 로 바꾸기(이미 replace 가 들어 있으면 건너뜀).
const RUST_PATCHES = [
  {
    id: 'hwpx-hf-autonum',
    file: 'src/serializer/hwpx/section.rs',
    anchor: '            c if (c as u32) < 0x20 => { /* 기타 제어문자 무시 */ }',
    insert: fs.readFileSync(path.join(HERE, 'patches', 'hwpx-hf-autonum.rs'), 'utf8'),
    done: '[claude-hwpx 패치]',
  },
  // rhwp#7419 — 줄 배치 없는 글자처럼 취급 표가 적힌 높이로 눌려 아래 표와 겹치는 것(patches/tac-no-ls-*.rs, devel 판은 개발 폴더 fix7419_devel.patch)
  ...['tac-no-ls-shrink', 'tac-no-ls-nested'].map((id) => {
    // git 이 체크아웃하며 CRLF 로 바꿔도 나눌 수 있게 LF 로 맞춘다(소스 쪽 줄바꿈은 아래에서 다시 맞춘다)
    const [find, replace] = fs.readFileSync(path.join(HERE, 'patches', `${id}.rs`), 'utf8').replace(/\r\n/g, '\n').split('\n// ==== replace ====\n');
    return { id, file: 'src/renderer/height_measurer.rs', find: find.replace(/^\/\/ ==== find ====\n/, ''), replace, done: `[claude-hwpx ${id}]` };
  }),
  // 문단 모양 대화상자에서 아무것도 안 바꾸고 설정을 눌러도 문단에 네 변 실선 상자가 생기던 것(patches/para-bf-base-*.rs)
  {
    id: 'para-bf-base',
    file: 'src/document_core/commands/formatting.rs',
    anchor: '    pub fn apply_para_format_native(',
    insert: fs.readFileSync(path.join(HERE, 'patches', 'para-bf-base-helper.rs'), 'utf8').replace(/\r\n/g, '\n'),
    done: '[claude-hwpx para-bf-base]',
  },
  ...['para-bf-base-body', 'para-bf-base-cell'].map((id) => {
    const [find, replace] = fs.readFileSync(path.join(HERE, 'patches', `${id}.rs`), 'utf8').replace(/\r\n/g, '\n').split('\n// ==== replace ====\n');
    return { id, file: 'src/document_core/commands/formatting.rs', find: find.replace(/^\/\/ ==== find ====\n/, ''), replace, done: `[claude-hwpx ${id}]` };
  }),
  // 표 오른쪽 끝(아래 끝)까지 셀을 합치면 없던 오른쪽(아래) 선이 생기던 것(patches/merge-edge-*.rs)
  ...[['merge-edge', '    pub fn merge_table_cells_native(', 'merge-edge-helper'],
    ['merge-edge-after', '        let reflow_cell: Option<(usize, usize)> = {', 'merge-edge-after']].map(([id, anchor, f]) => ({
    id, file: 'src/document_core/commands/table_ops.rs', anchor,
    insert: fs.readFileSync(path.join(HERE, 'patches', `${f}.rs`), 'utf8').replace(/\r\n/g, '\n'),
    done: `[claude-hwpx ${id}]`,
  })),
  // Ctrl+K,H/R/C — 표시 글을 감싼 필드(하이퍼링크, 상호 참조, 문서 요약) 넣기(patches/field-ex-*.rs)
  ...[['field-ex', 'src/document_core/queries/field_query.rs', 'fn insert_click_here_field_in_para(', 'field-ex-helper'],
    ['field-ex-method', 'src/document_core/queries/field_query.rs', '    /// getFieldList: 모든 필드를 JSON 배열로 반환', 'field-ex-method'],
    ['field-ex-wasm', 'src/wasm_api.rs', '    /// 현재 본문 위치에 ClickHere 누름틀 필드를 삽입한다.', 'field-ex-wasm']].map(([id, file, anchor, f]) => ({
    id, file, anchor,
    insert: fs.readFileSync(path.join(HERE, 'patches', `${f}.rs`), 'utf8').replace(/\r\n/g, '\n'),
    done: `[claude-hwpx ${id}]`,
  })),
  // 빈 머리말/꼬리말이 다시 열고 저장하면 문단 없는 subList 가 되어 한/글이 죽던 것(patches/hf-empty-para.rs)
  (() => {
    const [find, replace] = fs.readFileSync(path.join(HERE, 'patches', 'hf-empty-para.rs'), 'utf8').replace(/\r\n/g, '\n').split('\n// ==== replace ====\n');
    return { id: 'hf-empty-para', file: 'src/serializer/hwpx/section.rs', find: find.replace(/^\/\/ ==== find ====\n/, ''), replace, done: '[claude-hwpx hf-empty-para]' };
  })(),
  // 하이퍼링크, 날짜 필드 끝에 친 글이 필드 안으로 빨려 들던 것(patches/field-closed-edges.rs)
  (() => {
    const [find, replace] = fs.readFileSync(path.join(HERE, 'patches', 'field-closed-edges.rs'), 'utf8').replace(/\r\n/g, '\n').split('\n// ==== replace ====\n');
    return { id: 'field-closed-edges', file: 'src/model/paragraph.rs', find: find.replace(/^\/\/ ==== find ====\n/, ''), replace, done: '[claude-hwpx field-closed-edges]' };
  })(),
  (() => {
    const [find, replace] = fs.readFileSync(path.join(HERE, 'patches', 'merge-edge-before.rs'), 'utf8').replace(/\r\n/g, '\n').split('\n// ==== replace ====\n');
    return { id: 'merge-edge-before', file: 'src/document_core/commands/table_ops.rs', find: find.replace(/^\/\/ ==== find ====\n/, ''), replace, done: '[claude-hwpx merge-edge-before]' };
  })(),
  // 글자처럼 취급 개체(표, 그림, 수식) 뒤에서 입력, 삭제, 복사, 선택 음영이 한 칸씩 어긋나고 개체가 선택에 안 들던 것
  // (patches/caret-axis-*.rs). 캐럿 축 ↔ 글자, 나누기 축 변환, 캐럿 축 삭제, 복사, 음영. 스튜디오 쪽은 STUDIO_PATCHES
  ...[['caret-axis-helpers', 'src/document_core/helpers.rs', '/// ShapeObject에서 TextBox를 추출하는 헬퍼', 'fn caret_axis_items('],
    ['caret-axis-clip', 'src/document_core/commands/clipboard.rs', 'fn collect_max_clipboard_field_id(', 'fn remove_control_from_para('],
    ['caret-axis-copy', 'src/document_core/commands/clipboard.rs', '    /// 컨트롤 객체(표, 이미지, 도형)를 내부 클립보드에 복사한다.', 'fn copy_caret_paragraphs('],
    ['caret-axis-delete', 'src/document_core/commands/text_editing.rs', '    /// 표 셀에 대한 가변 참조를 얻는다.', 'fn delete_range_caret_native('],
    ['caret-axis-selbox-fn', 'src/document_core/queries/cursor_nav.rs', '/// 전체 중첩 경로가 같은 셀 컨테이너의 현재 문단을 가리키는지 확인한다.', 'fn caret_axis_find_control_box('],
    ['caret-axis-wasm', 'src/wasm_api.rs', '    /// 논리적 오프셋 → 텍스트 오프셋 변환.', 'js_name = convertCaretOffset']].map(([id, file, anchor, done]) => ({
    id, file, anchor, done,
    insert: fs.readFileSync(path.join(HERE, 'patches', `${id}.rs`), 'utf8').replace(/\r\n/g, '\n'),
  })),
  ...[['caret-axis-linestart', 'src/document_core/queries/cursor_nav.rs', 'utf16_pos_to_caret_idx(para, ls.text_start)'],
    ['caret-axis-selbox', 'src/document_core/queries/cursor_nav.rs', 'let mut hit_any = false;'],
    ['caret-axis-selsplit', 'src/document_core/queries/cursor_nav.rs', 'let mut hit_piece = false;'],
    ['caret-axis-insert', 'src/model/paragraph.rs', 'let after_inline = INSERT_AFTER_INLINE_CONTROLS'],
    ['caret-axis-paste-body', 'src/document_core/commands/clipboard.rs', '[claude-hwpx caret-axis paste-body]'],
    ['caret-axis-paste-cell', 'src/document_core/commands/clipboard.rs', '[claude-hwpx caret-axis paste-cell]'],
    ['caret-axis-html-body', 'src/document_core/commands/html_import.rs', '[claude-hwpx caret-axis html-body]'],
    ['caret-axis-html-cell', 'src/document_core/commands/html_import.rs', '[claude-hwpx caret-axis html-cell]']].map(([id, file, done]) => {
    const [find, replace] = fs.readFileSync(path.join(HERE, 'patches', `${id}.rs`), 'utf8').replace(/\r\n/g, '\n').split('\n// ==== replace ====\n');
    return { id, file, find: find.replace(/^\/\/ ==== find ====\n/, ''), replace, done };
  }),
  { id: 'caret-axis-insert-flag', file: 'src/model/paragraph.rs', anchor: '\nimpl Paragraph {\n', done: 'static INSERT_AFTER_INLINE_CONTROLS',
    insert: fs.readFileSync(path.join(HERE, 'patches', 'caret-axis-insert-flag.rs'), 'utf8').replace(/\r\n/g, '\n') },
  // 표 칸 문단에 글을 넣어도 줄 수가 그대로면 입력 전 줄 경계가 복원되어 한 줄에 몰리던 것(patches/cell-reflow-starts.rs)
  (() => {
    const [find, replace] = fs.readFileSync(path.join(HERE, 'patches', 'cell-reflow-starts.rs'), 'utf8').replace(/\r\n/g, '\n').split('\n// ==== replace ====\n');
    return { id: 'cell-reflow-starts', file: 'src/document_core/commands/text_editing.rs', find: find.replace(/^\/\/ ==== find ====\n/, ''), replace, done: '[claude-hwpx cell-reflow-starts]' };
  })(),
  // 칸 편집으로 글자처럼 취급 표가 커져도 쪽 나누기가 옛 줄 높이만 써서 쪽 끝 줄이 본문 밖으로 나가던 것(patches/tac-host-sync-*.rs)
  { id: 'tac-host-sync-measure', file: 'src/renderer/height_measurer.rs', anchor: '    /// 재귀적 높이 제한',
    insert: fs.readFileSync(path.join(HERE, 'patches', 'tac-host-sync-measure.rs'), 'utf8').replace(/\r\n/g, '\n'), done: '[claude-hwpx tac-host-sync] 편집한 표 하나' },
  { id: 'tac-host-sync-fn', file: 'src/document_core/commands/text_editing.rs', anchor: '    fn reflow_cell_paragraph_after_text_edit(',
    insert: fs.readFileSync(path.join(HERE, 'patches', 'tac-host-sync-fn.rs'), 'utf8').replace(/\r\n/g, '\n'), done: '글 없는 문단에 줄마다 표 하나' },
  (() => {
    // 입력과 삭제 두 경로에 같은 자리가 있어 모두 바꾼다(all)
    const [find, replace] = fs.readFileSync(path.join(HERE, 'patches', 'tac-host-sync-call.rs'), 'utf8').replace(/\r\n/g, '\n').split('\n// ==== replace ====\n');
    return { id: 'tac-host-sync-call', file: 'src/document_core/commands/text_editing.rs', find: find.replace(/^\/\/ ==== find ====\n/, ''), replace, all: true, done: '[claude-hwpx tac-host-sync] 표 높이가 바뀌었으면' };
  })(),
  // 칸 안 글자처럼 취급 표의 그림 크기를 바꾸면(자르기 등) 표 높이를 적힌 칸 높이 합으로 다시 세어 다른 칸이 눌리던 것(patches/cell-pic-delta-*.rs)
  { id: 'cell-pic-delta-before', file: 'src/document_core/commands/object_ops/table.rs', anchor: '        let caption_changed = {',
    insert: fs.readFileSync(path.join(HERE, 'patches', 'cell-pic-delta-before.rs'), 'utf8').replace(/\r\n/g, '\n'), done: '[claude-hwpx cell-pic-delta] 바꾸기 전' },
  (() => {
    const [find, replace] = fs.readFileSync(path.join(HERE, 'patches', 'cell-pic-delta-after.rs'), 'utf8').replace(/\r\n/g, '\n').split('\n// ==== replace ====\n');
    return { id: 'cell-pic-delta-after', file: 'src/document_core/commands/object_ops/table.rs', find: find.replace(/^\/\/ ==== find ====\n/, ''), replace, done: 'let mut claude_restored' };
  })(),
  // 글자처럼 취급 표를 끌면 남은 거리를 세로 위치에 적어 표가 다른 문단과 겹치던 것(patches/tac-table-move.rs)
  (() => {
    const [find, replace] = fs.readFileSync(path.join(HERE, 'patches', 'tac-table-move.rs'), 'utf8').replace(/\r\n/g, '\n').split('\n// ==== replace ====\n');
    return { id: 'tac-table-move', file: 'src/document_core/commands/table_ops.rs', find: find.replace(/^\/\/ ==== find ====\n/, ''), replace, done: '[claude-hwpx tac-table-move]' };
  })(),
  (() => {
    const [find, replace] = fs.readFileSync(path.join(HERE, 'patches', 'tac-table-move-ret.rs'), 'utf8').replace(/\r\n/g, '\n').split('\n// ==== replace ====\n');
    return { id: 'tac-table-move-ret', file: 'src/document_core/commands/table_ops.rs', find: find.replace(/^\/\/ ==== find ====\n/, ''), replace, done: '[claude-hwpx tac-table-move-ret]' };
  })(),
  // 표 칸 문단 안에 글자처럼 취급 그림 넣기(엔진은 칸 위에 뜬 그림으로만 넣었다, patches/cell-pic-inline-*.rs)
  ...['cell-pic-inline-a', 'cell-pic-inline-b', 'cell-pic-inline-c'].map((id) => {
    const [find, replace] = fs.readFileSync(path.join(HERE, 'patches', `${id}.rs`), 'utf8').replace(/\r\n/g, '\n').split('\n// ==== replace ====\n');
    return { id, file: 'src/document_core/commands/object_ops/picture.rs', find: find.replace(/^\/\/ ==== find ====\n/, ''), replace,
      done: id === 'cell-pic-inline-a' ? '[claude-hwpx cell-pic-inline] 표 칸' : `[claude-hwpx ${id}]` };
  }),
  // 표 칸 문단의 글자처럼 취급 그림 옆 캐럿이 첫 그림 가운데에 서던 것(patches/cell-inline-caret-*.rs)
  { id: 'cell-inline-caret-fn', file: 'src/document_core/queries/cursor_rect.rs', anchor: '    pub fn get_cursor_rect_in_cell_native(',
    insert: fs.readFileSync(path.join(HERE, 'patches', 'cell-inline-caret-fn.rs'), 'utf8').replace(/\r\n/g, '\n'), done: '[claude-hwpx cell-inline-caret] 표 칸' },
  ...['cell-inline-caret-call', 'cell-inline-caret-path'].map((id) => {
    const [find, replace] = fs.readFileSync(path.join(HERE, 'patches', `${id}.rs`), 'utf8').replace(/\r\n/g, '\n').split('\n// ==== replace ====\n');
    return { id, file: 'src/document_core/queries/cursor_rect.rs', find: find.replace(/^\/\/ ==== find ====\n/, ''), replace, done: `[claude-hwpx ${id}]` };
  }),
  (() => {
    // 칸 문단 나누기와 합치기 두 곳(all)
    const [find, replace] = fs.readFileSync(path.join(HERE, 'patches', 'tac-host-sync-split.rs'), 'utf8').replace(/\r\n/g, '\n').split('\n// ==== replace ====\n');
    return { id: 'tac-host-sync-split', file: 'src/document_core/commands/text_editing.rs', find: find.replace(/^\/\/ ==== find ====\n/, ''), replace, all: true, done: '[claude-hwpx tac-host-sync-split]' };
  })(),
  // 쪽 나누기 시작에 편집한(dirty) 글자처럼 취급 표를 모두 맞춘다 — 편집 경로마다 부르면 빠지는 곳이 생겼다(patches/tac-host-sync-paginate.rs, -deferred.rs)
  ...['tac-host-sync-paginate', 'tac-host-sync-deferred'].map((id) => {
    const [find, replace] = fs.readFileSync(path.join(HERE, 'patches', `${id}.rs`), 'utf8').replace(/\r\n/g, '\n').split('\n// ==== replace ====\n');
    return { id, file: 'src/document_core/queries/rendering.rs', find: find.replace(/^\/\/ ==== find ====\n/, ''), replace, done: `[claude-hwpx ${id}]` };
  }),
  // 바꾸기로 칸 글이 바뀌어도 표에 dirty 가 안 켜져 표가 늘지 않던 것(patches/replace-cell-dirty.rs)
  (() => {
    const [find, replace] = fs.readFileSync(path.join(HERE, 'patches', 'replace-cell-dirty.rs'), 'utf8').replace(/\r\n/g, '\n').split('\n// ==== replace ====\n');
    return { id: 'replace-cell-dirty', file: 'src/document_core/queries/search_query.rs', find: find.replace(/^\/\/ ==== find ====\n/, ''), replace, done: '[claude-hwpx replace-cell-dirty]' };
  })(),
  // 편집 뒤 표 높이는 처음 쪽을 나눌 때 잰 어긋남(rhwp 측정 − 한글이 적은 높이)을 뺀다 — 칸 안 표 등을 한글보다 크게 재어
  // 칸을 한 번만 고쳐도 표가 한글보다 9~32px 커지던 것(patches/tac-sync-offset-*.rs, 계산은 tac-host-sync-fn.rs)
  ...[['tac-sync-offset-field', 'src/model/table.rs', 'tac-sync-offset-field', 'pub claude_measure_offset'],
    ['tac-sync-offset-sweep', 'src/diagnostics/ir_field_sweep.rs', 'tac-sync-offset-sweep', 'claude_measure_offset: _,'],
    ['tac-sync-offset-init-a', 'src/document_core/commands/object_ops/table.rs', 'tac-sync-offset-init', 'claude_measure_offset: None'],
    ['tac-sync-offset-init-b', 'src/document_core/html_table_import.rs', 'tac-sync-offset-init', 'claude_measure_offset: None'],
    ['tac-sync-offset-init-c', 'src/scaffold/builder.rs', 'tac-sync-offset-init8', 'claude_measure_offset: None']].map(([id, file, f, done]) => {
    const [find, replace] = fs.readFileSync(path.join(HERE, 'patches', `${f}.rs`), 'utf8').replace(/\r\n/g, '\n').split('\n// ==== replace ====\n');
    return { id, file, find: find.replace(/^\/\/ ==== find ====\n/, ''), replace: replace.replace(/\n$/, ''), all: true, done };
  }),
  // 표 옆 글을 고쳐 줄을 다시 나누면 글자처럼 취급 표 줄에서 바깥 여백이 빠지던 것(patches/tac-line-outer.rs)
  // 표, 그림 끌어 옮기기를 놓을 때 개체를 그 문단 자리로 옮긴다(patches/move-control-para*.rs, 스튜디오 move-drop-line.ts)
  { id: 'move-control-para', file: 'src/document_core/commands/clipboard.rs', anchor: '    /// 컨트롤 객체(표, 이미지, 도형)를 내부 클립보드에 복사한다.\n    pub fn copy_control_native(',
    insert: fs.readFileSync(path.join(HERE, 'patches', 'move-control-para.rs'), 'utf8').replace(/\r\n/g, '\n'), done: '[claude-hwpx move-control-para] 본문 개체' },
  // move-control-para.rs 안에 들어 있는 수정(떠 있는 그림, 도형 문단의 줄 높이). 이름을 목록에 두어 이 수정 전에 빌드한 WASM 을 다시 빌드하게 한다
  { id: 'move-float-line', file: 'src/document_core/commands/clipboard.rs', find: '[claude-hwpx move-float-line]', replace: '', done: '[claude-hwpx move-float-line]' },
  { id: 'move-band', file: 'src/document_core/commands/clipboard.rs', find: '[claude-hwpx move-band]', replace: '', done: '[claude-hwpx move-band]' },
  { id: 'move-release-band', file: 'src/document_core/commands/clipboard.rs', find: '[claude-hwpx move-release-band]', replace: '', done: '[claude-hwpx move-release-band]' },
  { id: 'move-control-para-wasm', file: 'src/wasm_api.rs', anchor: '    /// [claude-hwpx caret-axis] 켜 두는 동안',
    insert: fs.readFileSync(path.join(HERE, 'patches', 'move-control-para-wasm.rs'), 'utf8').replace(/\r\n/g, '\n'), done: 'js_name = moveControlToParagraph' },
  // 칸 안 두 그림 사이에 친 글이 둘째 그림 뒤로 가던 것(patches/insert-after-count-pos.rs, 나머지는 caret-axis-insert*, -helpers, -wasm, -bridge 안)
  (() => {
    const [find, replace] = fs.readFileSync(path.join(HERE, 'patches', 'insert-after-count-pos.rs'), 'utf8').replace(/\r\n/g, '\n').split('\n// ==== replace ====\n');
    return { id: 'insert-after-count-pos', file: 'src/model/paragraph.rs', find: find.replace(/^\/\/ ==== find ====\n/, ''), replace: replace.replace(/\n$/, ''), done: '[claude-hwpx insert-after-count-pos]' };
  })(),
  // 그림만 있는 칸 문단을 누르면 캐럿이 첫 그림 안쪽에 서던 것(patches/cell-pic-hit-*.rs, 캐럿 좌표는 cell-inline-caret-fn)
  { id: 'cell-pic-hit-fn', file: 'src/document_core/queries/cursor_rect.rs', anchor: '    /// 페이지 좌표에서 문서 위치 찾기 (네이티브)\n    pub fn hit_test_native(',
    insert: fs.readFileSync(path.join(HERE, 'patches', 'cell-pic-hit-fn.rs'), 'utf8').replace(/\r\n/g, '\n'), done: '[claude-hwpx cell-pic-hit] 글 없이' },
  ...[['cell-pic-hit-call', '[claude-hwpx cell-pic-hit] 그림만 있는'], ['cell-pic-hit-cell', '[claude-hwpx cell-pic-hit-cell]']].map(([id, done]) => {
    const [find, replace] = fs.readFileSync(path.join(HERE, 'patches', `${id}.rs`), 'utf8').replace(/\r\n/g, '\n').split('\n// ==== replace ====\n');
    return { id, file: 'src/document_core/queries/cursor_rect.rs', find: find.replace(/^\/\/ ==== find ====\n/, ''), replace: replace.replace(/\n$/, ''), done };
  }),
  // 글자처럼 취급 표의 행 높이를 저장 줄 배치 사다리로 정한다(patches/tac-row-ladder.rs)
  (() => {
    const [find, replace] = fs.readFileSync(path.join(HERE, 'patches', 'tac-row-ladder.rs'), 'utf8').replace(/\r\n/g, '\n').split('\n// ==== replace ====\n');
    return { id: 'tac-row-ladder', file: 'src/renderer/height_measurer.rs', find: find.replace(/^\/\/ ==== find ====\n/, ''), replace: replace.replace(/\n$/, ''), done: '[claude-hwpx tac-row-ladder]' };
  })(),
  ...['tac-line-outer', 'tac-line-outer-size'].map((id) => {
    const [find, replace] = fs.readFileSync(path.join(HERE, 'patches', `${id}.rs`), 'utf8').replace(/\r\n/g, '\n').split('\n// ==== replace ====\n');
    return { id, file: 'src/renderer/composer/line_breaking.rs', find: find.replace(/^\/\/ ==== find ====\n/, ''), replace: replace.replace(/\n$/, ''), done: `[claude-hwpx ${id}]` };
  }),
  // 칸 크기 조절에 표 높이를 함께 받는다 — Ctrl+위/아래로 고른 행만 키워도 모든 행이 비례로 커지던 것(patches/row-resize-th-*.rs, 스튜디오 row-resize-rendered.ts)
  ...['row-resize-th-parse', 'row-resize-th-apply'].map((id) => {
    const [find, replace] = fs.readFileSync(path.join(HERE, 'patches', `${id}.rs`), 'utf8').replace(/\r\n/g, '\n').split('\n// ==== replace ====\n');
    return { id, file: 'src/document_core/commands/table_ops.rs', find: find.replace(/^\/\/ ==== find ====\n/, ''), replace, done: id === 'row-resize-th-parse' ? 'let claude_table_height' : 'if claude_table_height.is_some()' };
  }),
  // 가운데 정렬 문단을 첫 글자부터 고르면 선택 음영이 줄 왼쪽 여백부터 칠해지던 것(patches/sel-left-at-glyph.rs)
  (() => {
    const [find, replace] = fs.readFileSync(path.join(HERE, 'patches', 'sel-left-at-glyph.rs'), 'utf8').replace(/\r\n/g, '\n').split('\n// ==== replace ====\n');
    return { id: 'sel-left-at-glyph', file: 'src/document_core/queries/cursor_nav.rs', find: find.replace(/^\/\/ ==== find ====\n/, ''), replace, done: '[claude-hwpx sel-left-at-glyph]' };
  })(),
  // 글자처럼 취급하지 않는 그림의 본문 배치 — 편집 뒤에도 글이 그림을 비키게(patches/wrap-*.rs).
  // 파일 하나에 조각 여럿(// ==== next ====). 이미 들어간 조각은 바꾼 글이 소스에 있는지로 안다
  ...[
    ['wrap-band-fragment', 'src/renderer/height_measurer.rs'],
    ['wrap-side-policy', 'src/renderer/layout_frame.rs'],
    ['wrap-exclusion', 'src/renderer/float_placement.rs'],
    ['wrap-exclusion-tests', 'src/renderer/float_placement.rs'],
    ['wrap-page-exclusion', 'src/renderer/float_placement.rs'],
    ['wrap-page-band', 'src/renderer/composer/line_breaking.rs'],
    ['wrap-band-lead', 'src/document_core/commands/text_editing.rs'],
    ['wrap-page-edit', 'src/document_core/commands/text_editing.rs'],
    ['wrap-local-edit', 'src/document_core/commands/text_editing.rs'],
    ['wrap-para-offset', 'src/renderer/layout.rs'],
    ['wrap-behind-advance', 'src/renderer/layout.rs'],
    ['wrap-band-host-ladder', 'src/renderer/layout.rs'],
    ['wrap-band-owner-pub', 'src/document_core/commands/text_editing.rs'],
    ['wrap-band-page-end', 'src/renderer/composer/line_breaking.rs'],
    ['wrap-split-follower', 'src/renderer/layout/paragraph_layout.rs'],
    ['wrap-margin-box', 'src/renderer/float_placement.rs'],
    ['wrap-props-release', 'src/document_core/commands/object_ops/picture.rs'],
    ['wrap-tab-empty-host', 'src/renderer/composer/line_breaking.rs'],
    ['wrap-band-backward', 'src/renderer/composer/line_breaking.rs'],
    ['wrap-band-backward-edit', 'src/document_core/commands/text_editing.rs'],
    ['wrap-text-flow-props', 'src/document_core/commands/object_ops/picture.rs'],
  ].flatMap(([id, file]) => {
    const blocks = fs.readFileSync(path.join(HERE, 'patches', `${id}.rs`), 'utf8').replace(/\r\n/g, '\n')
      .replace(/^\/\/ ==== find ====\n/, '').split('\n// ==== next ====\n').map((b) => b.split('\n// ==== replace ====\n'));
    // 뒤 패치가 앞 패치의 코드를 고쳐 쓰기도 해서 「바꾼 글이 소스에 있는가」로는 이미 넣었는지 알 수 없다(다시 넣다가 멈추거나
    // 두 번 넣었다). 첫 조각의 표식([claude-hwpx …])이 소스에 있으면 그 파일의 조각을 모두 넣은 것으로 본다
    // 조각들은 한 묶음(blocks)으로 넣는다 — 조각마다 판단하면 첫 조각이 표식을 넣은 뒤 나머지 조각을 건너뛰었다
    const marker = (blocks[0][1].match(/\[claude-hwpx [\w-]+\]/) ?? [])[0];
    const parts = blocks.map(([find, replace]) => ({ find, replace: replace.replace(/\n$/, '') }));
    return [{ id, file, blocks: parts, done: marker ?? parts[0].replace }];
  }),
];
const builtMark = path.join(pkgDir, '.claude-patched');
const builtIds = fs.existsSync(builtMark) ? fs.readFileSync(builtMark, 'utf8') : '';
if (hasRust && RUST_PATCHES.some((p) => !builtIds.includes(p.id))) {
  for (const p of RUST_PATCHES) {
    const f = path.join(RHWP, p.file);
    let src = fs.readFileSync(f, 'utf8');
    if (src.replace(/\r\n/g, '\n').includes(p.done)) continue;
    const eol = (s) => (src.includes('\r\n') ? s.replace(/\r?\n/g, '\r\n') : s);   // 태그 판 소스는 CRLF 다
    if (p.blocks) {
      for (const [i, b] of p.blocks.entries()) {
        if (src.split(eol(b.find)).length !== 2) throw new Error(`${p.file} 에서 패치 자리(${p.id} 조각 ${i + 1})를 하나로 못 찾았다 — rhwp 버전이 바뀌었거나 옛 패치가 남았다면 --clean`);
        src = src.replace(eol(b.find), () => eol(b.replace));
      }
      fs.writeFileSync(f, src);
      continue;
    }
    const at = eol(p.anchor ?? p.find);
    if (!src.includes(at)) throw new Error(`${p.file} 에서 패치 자리(${p.id})를 못 찾았다 — rhwp 버전이 바뀌었는지 확인`);
    src = p.anchor ? src.replace(at, eol(p.insert) + at) : p.all ? src.split(at).join(eol(p.replace)) : src.replace(at, eol(p.replace));
    fs.writeFileSync(f, src);
  }
  const env = { ...process.env, PATH: `${cargoBin}${path.delimiter}${process.env.PATH}` };
  exec(path.join(cargoBin, 'wasm-pack'), ['build', '--target', 'web', '--release', '--locked', '--out-dir', 'pkg'], { cwd: RHWP, env });
  fs.writeFileSync(builtMark, `rhwp ${RHWP_VERSION} + ${RUST_PATCHES.map((p) => p.id).join(', ')}\n`);
} else if (!hasRust && !fs.existsSync(path.join(pkgDir, 'rhwp_bg.wasm'))) {
  fs.mkdirSync(pkgDir, { recursive: true });
  sh(`npm pack @rhwp/core@${RHWP_VERSION} --silent`, BUILD);
  sh(`tar -xzf rhwp-core-${RHWP_VERSION}.tgz`, BUILD);
  for (const f of fs.readdirSync(path.join(BUILD, 'package'))) {
    if (f.startsWith('rhwp')) fs.copyFileSync(path.join(BUILD, 'package', f), path.join(pkgDir, f));
  }
  rmrf(path.join(BUILD, 'package'));
  rmrf(path.join(BUILD, `rhwp-core-${RHWP_VERSION}.tgz`));
}

// 3. claude 플러그인 복사와 allowlist 등록
for (const f of ['claude-plugin.ts', 'hancom-keys.ts', 'edit-log.ts', 'k-commands.ts', 'log-panel.ts', 'color-palette.ts', 'para-preview.ts', 'dialog-enter.ts', 'cell-block-erase.ts', 'picture-crop.ts', 'move-drop.ts']) fs.copyFileSync(path.join(HERE, 'plugin', f), path.join(STUDIO, 'src', 'plugin', f));
// 편집 도구 라이브러리(lib/SOURCE.md)도 같은 자리로. 플러그인이 './doc-tools.js' 로 부른다.
for (const f of ['doc-tools.js', 'doc-rules.js', 'collab-ops.js']) {
  fs.copyFileSync(path.join(HERE, 'plugin', 'lib', f), path.join(STUDIO, 'src', 'plugin', f));
}
const mainTs = path.join(STUDIO, 'src', 'main.ts');
let main = fs.readFileSync(mainTs, 'utf8');
// 커서 조회, 위치 이동에 inputHandler 가 필요한데 PluginHost 에는 없어서 클로저로 넘긴다.
const REGISTER = "  if (id === 'claude') {\n    return (await import('@/plugin/claude-plugin')).createClaudePlugin(() => inputHandler) as StudioPlugin;\n  }\n";
main = main.replace(/  if \(id === 'claude'\) \{\n.*\n  \}\n/, '');   // 옛 등록(claudePlugin 상수)을 걷어 낸다
if (!main.includes(REGISTER)) {
  const anchor = "  if (import.meta.env.DEV && id === 'dev-probe') {";
  if (!main.includes(anchor)) throw new Error('main.ts 에서 플러그인 allowlist 자리를 못 찾았다 — rhwp 버전이 바뀌었는지 확인');
  main = main.replace(anchor, REGISTER + anchor);
}
fs.writeFileSync(mainTs, main);

// 스튜디오 소스 패치(patches/*.ts). 캐럿 축 연결은 wasm-bridge.ts 끝에 덧붙인다 — 엔진 패치 caret-axis-* 와 짝
for (const p of [{ id: 'caret-axis-bridge', file: 'src/core/wasm-bridge.ts', done: '[claude-hwpx caret-axis] 캐럿 축 연결.' }]) {
  const f = path.join(STUDIO, p.file);
  const block = fs.readFileSync(path.join(HERE, 'patches', `${p.id}.ts`), 'utf8').replace(/\r\n/g, '\n');
  let src = fs.readFileSync(f, 'utf8');
  const at = src.indexOf(p.done);
  if (at >= 0) src = src.slice(0, src.lastIndexOf('\n', src.lastIndexOf('\n', at) - 1) + 1);   // 옛 판을 걷고 새로 붙인다
  fs.writeFileSync(f, src.replace(/\n*$/, '\n') + block);
}
// Backspace, Delete 로 지울 한 칸이 글자처럼 취급 개체면 선택 삭제 명령으로(개체까지 지우고 되돌리기에서 개체도 돌아온다).
// 한 글자 삭제 명령은 되돌리기용으로 글자만 저장한다 — 연결층의 isCaretControlSlot 과 짝
{
  const f = path.join(STUDIO, 'src', 'engine', 'input-handler-text.ts');
  let src = fs.readFileSync(f, 'utf8');
  if (!src.includes('isCaretControlSlot')) {
    const edits = [
      ['  DeleteTextCommand,\n  MergeParagraphCommand,', '  DeleteTextCommand,\n  DeleteSelectionCommand,\n  MergeParagraphCommand,'],
      ["command: new DeleteTextCommand(deletePos, 1, 'backward') });",
        "command: this.wasm.isCaretControlSlot?.(deletePos) ? new DeleteSelectionCommand(deletePos, pos) : new DeleteTextCommand(deletePos, 1, 'backward') }); // [claude-hwpx caret-axis]"],
      ["command: new DeleteTextCommand(pos, 1, 'forward') });",
        "command: this.wasm.isCaretControlSlot?.(pos) ? new DeleteSelectionCommand(pos, { ...pos, charOffset: pos.charOffset + 1 }) : new DeleteTextCommand(pos, 1, 'forward') }); // [claude-hwpx caret-axis]"],
    ];
    const eol = (s) => (src.includes('\r\n') ? s.replace(/\r?\n/g, '\r\n') : s);
    for (const [find, replace] of edits) {
      if (!src.includes(eol(find))) throw new Error(`input-handler-text.ts 에서 패치 자리를 못 찾았다: ${find.slice(0, 40)}`);
      src = src.split(eol(find)).join(eol(replace));
    }
    fs.writeFileSync(f, src);
  }
}

// 여러 줄에 걸친 병합 칸이 있는 셀 블록을 Shift+방향키로 경계 이동하면 병합 칸 옆 둘째 줄부터 이웃이 안 줄어 표가 뒤틀리던 것
// (patches/boundary-resize-merged.ts). 스튜디오 소스를 찾아 바꾼다
{
  const f = path.join(STUDIO, 'src', 'engine', 'table-resize-updates.ts');
  let src = fs.readFileSync(f, 'utf8');
  if (!src.includes('[claude-hwpx boundary-merged]')) {
    const [find, replace] = fs.readFileSync(path.join(HERE, 'patches', 'boundary-resize-merged.ts'), 'utf8').replace(/\r\n/g, '\n')
      .replace(/^\/\/ ==== find ====\n/, '').split('\n// ==== replace ====\n');
    const eol = (s) => (src.includes('\r\n') ? s.replace(/\r?\n/g, '\r\n') : s);
    if (src.split(eol(find)).length !== 2) throw new Error('table-resize-updates.ts 에서 패치 자리(boundary-merged)를 하나로 못 찾았다');
    fs.writeFileSync(f, src.replace(eol(find), eol(replace)));
  }
}

// 표 끌기 되돌리기가 거리를 반대로 끄는 방식이라 제자리로 오지 않던 것, 글자처럼 취급 표 끌기의 남은 거리 넘기기(patches/table-move-undo.ts)
{
  const f = path.join(STUDIO, 'src', 'engine', 'input-handler-table.ts');
  let src = fs.readFileSync(f, 'utf8');
  if (!src.includes('[claude-hwpx table-move-undo]')) {
    const eol = (s) => (src.includes('\r\n') ? s.replace(/\r?\n/g, '\r\n') : s);
    const blocks = fs.readFileSync(path.join(HERE, 'patches', 'table-move-undo.ts'), 'utf8').replace(/\r\n/g, '\n')
      .replace(/^\/\/ ==== find ====\n/, '').split('\n// ==== next ====\n');
    for (const b of blocks) {
      const [find, replace] = b.split('\n// ==== replace ====\n');
      if (src.split(eol(find)).length !== 2) throw new Error('input-handler-table.ts 에서 패치 자리(table-move-undo)를 하나로 못 찾았다');
      src = src.replace(eol(find), eol(replace));
    }
    fs.writeFileSync(f, src);
  }
}

// 표, 그림 끌어 옮기기: 끄는 동안 푸른 선만, 놓을 때 문단 자리로 옮긴다(patches/move-drop-*.ts, plugin/move-drop.ts, 엔진 move-control-para)
for (const [file, patch] of [['input-handler-table.ts', 'move-drop-table.ts'], ['input-handler-picture.ts', 'move-drop-picture.ts'], ['input-handler-mouse.ts', 'move-drop-mouse.ts']]) {
  const f = path.join(STUDIO, 'src', 'engine', file);
  let src = fs.readFileSync(f, 'utf8');
  if (src.includes('[claude-hwpx move-drop-line]')) continue;
  const eol = (t) => (src.includes('\r\n') ? t.replace(/\r?\n/g, '\r\n') : t);
  const blocks = fs.readFileSync(path.join(HERE, 'patches', patch), 'utf8').replace(/\r\n/g, '\n')
    .replace(/^\/\/ ==== find ====\n/, '').split('\n// ==== next ====\n');
  for (const b of blocks) {
    const [find, replace] = b.split('\n// ==== replace ====\n');
    if (src.split(eol(find)).length !== 2) throw new Error(`${file} 에서 패치 자리(${patch})를 하나로 못 찾았다`);
    src = src.replace(eol(find), () => eol(replace.replace(/\n$/, '')));
  }
  fs.writeFileSync(f, src);
}

// Ctrl+방향키 칸/줄 전체 조절에 최소 크기 검사가 없어 줄일 수 없는 크기에서 칸마다 따로 멈추며 어긋나던 것(patches/column-resize-min.ts)
{
  const f = path.join(STUDIO, 'src', 'engine', 'table-resize-updates.ts');
  let src = fs.readFileSync(f, 'utf8');
  if (!src.includes('[claude-hwpx column-resize-min]')) {
    const [find, replace] = fs.readFileSync(path.join(HERE, 'patches', 'column-resize-min.ts'), 'utf8').replace(/\r\n/g, '\n')
      .replace(/^\/\/ ==== find ====\n/, '').split('\n// ==== replace ====\n');
    const eol = (s) => (src.includes('\r\n') ? s.replace(/\r?\n/g, '\r\n') : s);
    if (src.split(eol(find)).length !== 2) throw new Error('table-resize-updates.ts 에서 패치 자리(column-resize-min)를 하나로 못 찾았다');
    fs.writeFileSync(f, src.replace(eol(find), eol(replace)));
  }
}

// Ctrl+위/아래는 고른 행을 그려진 높이에서 한 단계 바꾸고 표 높이도 함께 보낸다(patches/row-resize-rendered.ts, 엔진 row-resize-th-*)
{
  const f = path.join(STUDIO, 'src', 'engine', 'input-handler-table.ts');
  let src = fs.readFileSync(f, 'utf8');
  if (!src.includes('[claude-hwpx row-resize-rendered]')) {
    const [find, replace] = fs.readFileSync(path.join(HERE, 'patches', 'row-resize-rendered.ts'), 'utf8').replace(/\r\n/g, '\n')
      .replace(/^\/\/ ==== find ====\n/, '').split('\n// ==== replace ====\n');
    const eol = (s) => (src.includes('\r\n') ? s.replace(/\r?\n/g, '\r\n') : s);
    if (src.split(eol(find)).length !== 2) throw new Error('input-handler-table.ts 에서 패치 자리(row-resize-rendered)를 하나로 못 찾았다');
    fs.writeFileSync(f, src.replace(eol(find), eol(replace)));
  }
}

// 그림 속성의 「본문과의 배치」 단추를 아이콘 대신 글자로(patches/wrap-text-labels.ts), 「본문 위치」 고르기(wrap-text-flow.ts),
// 오른쪽/아래 정렬 개체를 끄는 방향대로 옮기기(wrap-move-sign.ts)
for (const [id, rel] of [['wrap-text-labels', 'ui/picture-props-dialog.ts'], ['wrap-text-flow', 'ui/picture-props-dialog.ts'], ['wrap-move-sign', 'engine/input-handler-picture.ts']]) {
  const f = path.join(STUDIO, 'src', ...rel.split('/'));
  let src = fs.readFileSync(f, 'utf8');
  if (src.includes(`[claude-hwpx ${id}]`)) continue;
  const eol = (s) => (src.includes('\r\n') ? s.replace(/\r?\n/g, '\r\n') : s);
  const blocks = fs.readFileSync(path.join(HERE, 'patches', `${id}.ts`), 'utf8').replace(/\r\n/g, '\n')
    .replace(/^\/\/ ==== find ====\n/, '').split('\n// ==== next ====\n');
  for (const b of blocks) {
    const [find, replace] = b.split('\n// ==== replace ====\n');
    if (src.split(eol(find)).length !== 2) throw new Error(`${rel} 에서 패치 자리(${id})를 하나로 못 찾았다`);
    src = src.replace(eol(find), () => eol(replace.replace(/\n$/, '')));
  }
  fs.writeFileSync(f, src);
}

// 4. 빌드
if (!fs.existsSync(path.join(STUDIO, 'node_modules'))) sh('npm ci --no-audit --no-fund', STUDIO);
const nodeBin = (rel, ...args) => exec(process.execPath, [path.join(STUDIO, 'node_modules', rel), ...args], { cwd: STUDIO });
nodeBin('typescript/bin/tsc');
// vite 가 outDir 를 비울 때도 같은 크래시가 난다. 미리 지워 둔다.
rmrf(path.join(STUDIO, 'dist'));
nodeBin('vite/bin/vite.js', 'build', '--base=/studio/');

// 5. 산출물 배치
const dist = path.join(HERE, 'studio-dist');
rmrf(dist);
copyDir(path.join(STUDIO, 'dist'), dist);
// 서비스 워커는 옛 빌드를 캐시해 재빌드가 안 보이게 만든다. 로컬 브리지에는 필요 없다.
for (const f of fs.readdirSync(dist)) if (/^(sw|workbox-.*|registerSW)\.js$/.test(f)) fs.writeFileSync(path.join(dist, f), '');
// 서버가 Node 에서 같은 WASM 을 돌리도록(rhwp_layout.mjs, 한글이 없을 때 표 높이 보정) 짝이 맞는 JS 와 WASM 을 둔다.
// studio-dist/rhwp.js 는 번들과 짝이 다르다 — 쓰면 "function import requires a callable" 로 초기화가 실패한다.
fs.mkdirSync(path.join(dist, 'node'), { recursive: true });
for (const f of ['rhwp.js', 'rhwp_bg.wasm']) fs.copyFileSync(path.join(pkgDir, f), path.join(dist, 'node', f));

const sdk = path.join(HERE, 'sdk');
fs.mkdirSync(sdk, { recursive: true });
for (const f of ['index.js', 'transport.js', 'document-agent-contract.js']) {
  fs.copyFileSync(path.join(RHWP, 'npm', 'editor', f), path.join(sdk, f));
}
console.log(`\n완료: rhwp ${RHWP_VERSION} + claude 플러그인 → ${dist}`);
