#!/usr/bin/env node
/**
 * rhwp-studio 를 claude 플러그인을 넣어 빌드하고 studio-dist/, sdk/ 를 만든다.
 * Rust 툴체인은 필요 없다 — WASM 은 같은 버전의 npm @rhwp/core prebuilt 를 쓴다.
 *
 *   node setup.mjs            (이미 받은 소스가 있으면 재사용)
 *   node setup.mjs --clean    (.build 를 지우고 처음부터)
 *
 * rhwp 버전을 올릴 때는 RHWP_VERSION 만 바꾸고 --clean 으로 다시 돌린다.
 */
import fs from 'node:fs';
import path from 'node:path';
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

// 2. prebuilt WASM → ../pkg (studio 의 vite alias 가 여기를 본다)
const pkgDir = path.join(RHWP, 'pkg');
if (!fs.existsSync(path.join(pkgDir, 'rhwp_bg.wasm'))) {
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
fs.copyFileSync(path.join(HERE, 'plugin', 'claude-plugin.ts'), path.join(STUDIO, 'src', 'plugin', 'claude-plugin.ts'));
const mainTs = path.join(STUDIO, 'src', 'main.ts');
let main = fs.readFileSync(mainTs, 'utf8');
const MARK = "if (id === 'claude')";
if (!main.includes(MARK)) {
  const anchor = "  if (import.meta.env.DEV && id === 'dev-probe') {";
  if (!main.includes(anchor)) throw new Error('main.ts 에서 플러그인 allowlist 자리를 못 찾았다 — rhwp 버전이 바뀌었는지 확인');
  main = main.replace(anchor, `  ${MARK} {\n    return (await import('@/plugin/claude-plugin')).claudePlugin as StudioPlugin;\n  }\n${anchor}`);
  fs.writeFileSync(mainTs, main);
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

const sdk = path.join(HERE, 'sdk');
fs.mkdirSync(sdk, { recursive: true });
for (const f of ['index.js', 'transport.js', 'document-agent-contract.js']) {
  fs.copyFileSync(path.join(RHWP, 'npm', 'editor', f), path.join(sdk, f));
}
console.log(`\n완료: rhwp ${RHWP_VERSION} + claude 플러그인 → ${dist}`);
