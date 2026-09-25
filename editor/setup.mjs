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
const RUST_PATCHES = [
  {
    file: 'src/serializer/hwpx/section.rs',
    anchor: '            c if (c as u32) < 0x20 => { /* 기타 제어문자 무시 */ }',
    insert: fs.readFileSync(path.join(HERE, 'patches', 'hwpx-hf-autonum.rs'), 'utf8'),
  },
];
const builtMark = path.join(pkgDir, '.claude-patched');
if (hasRust && !fs.existsSync(builtMark)) {
  for (const p of RUST_PATCHES) {
    const f = path.join(RHWP, p.file);
    let src = fs.readFileSync(f, 'utf8');
    if (src.includes('[claude-hwpx 패치]')) continue;
    if (!src.includes(p.anchor)) throw new Error(`${p.file} 에서 패치 자리를 못 찾았다 — rhwp 버전이 바뀌었는지 확인`);
    src = src.replace(p.anchor, p.insert + p.anchor);
    fs.writeFileSync(f, src);
  }
  const env = { ...process.env, PATH: `${cargoBin}${path.delimiter}${process.env.PATH}` };
  exec(path.join(cargoBin, 'wasm-pack'), ['build', '--target', 'web', '--release', '--locked', '--out-dir', 'pkg'], { cwd: RHWP, env });
  fs.writeFileSync(builtMark, `rhwp ${RHWP_VERSION} + ${RUST_PATCHES.map((p) => p.file).join(', ')}\n`);
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
for (const f of ['claude-plugin.ts', 'hancom-keys.ts']) fs.copyFileSync(path.join(HERE, 'plugin', f), path.join(STUDIO, 'src', 'plugin', f));
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
