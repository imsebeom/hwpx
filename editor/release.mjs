#!/usr/bin/env node
/**
 * 이 PC 에서 빌드한 에디터(studio-dist, sdk)를 GitHub 릴리스로 올리고 prebuilt.json 을 갱신한다(관리자용).
 *   node setup.mjs --build   (원본을 고쳤으면 먼저 빌드)
 *   node release.mjs          → 릴리스 editor-<지문 12자> 를 저장소마다 만들고 zip 을 붙인다. 그 뒤 prebuilt.json 을 커밋, 푸시한다
 * gh CLI 로그인이 필요하다. 저장소는 REPOS 에 적는다.
 */
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { MANIFEST, packDist, sourceHash } from './prebuilt.mjs';

const REPOS = ['imsebeom/hwpx', 'imsebeom/hwpx2'];
const HERE = path.dirname(MANIFEST);
const hash = sourceHash();
const stamp = path.join(HERE, 'studio-dist', '.source-hash');
const built = fs.existsSync(stamp) ? fs.readFileSync(stamp, 'utf8').trim() : '';
if (built !== hash) {
  console.error(`studio-dist 가 지금 원본으로 빌드한 것이 아니다(${built.slice(0, 12) || '표식 없음'} ≠ ${hash.slice(0, 12)}). node setup.mjs --build 부터`);
  process.exit(1);
}

const tag = `editor-${hash.slice(0, 12)}`;
const asset = `hwpx-editor-${hash.slice(0, 12)}.zip`;
const zip = packDist();
const file = path.join(os.tmpdir(), asset);
fs.writeFileSync(file, zip);
const sha256 = crypto.createHash('sha256').update(zip).digest('hex');
console.log(`묶음: ${asset} ${(zip.length / 1048576).toFixed(1)} MB`);

const gh = (args) => spawnSync('gh', args, { encoding: 'utf8' });
for (const repo of REPOS) {
  const notes = `hwpx 스킬 에디터 모드 미리 빌드 묶음(studio-dist, sdk). rhwp 0.8.6 + editor/patches 엔진 패치.\n원본 지문 ${hash}\nsetup.mjs 가 지문이 같으면 이것을 받아 쓴다(Rust 없이도 패치가 든 엔진).`;
  let r = gh(['release', 'view', tag, '--repo', repo]);
  r = r.status === 0
    ? gh(['release', 'upload', tag, file, '--clobber', '--repo', repo])
    : gh(['release', 'create', tag, file, '--repo', repo, '--title', `에디터 묶음 ${hash.slice(0, 12)}`, '--notes', notes, '--latest=false']);
  if (r.status !== 0) { console.error(`${repo}: ${r.stderr || r.stdout}`); process.exit(1); }
  console.log(`${repo}: ${tag}`);
}

const manifest = {
  sourceHash: hash, sha256, tag, asset, rhwp: '0.8.6', builtAt: new Date().toISOString(),
  urls: REPOS.map((repo) => `https://github.com/${repo}/releases/download/${tag}/${asset}`),
};
fs.writeFileSync(MANIFEST, JSON.stringify(manifest, null, 2) + '\n');
fs.unlinkSync(file);
console.log(`prebuilt.json 갱신 — 커밋, 푸시하면 공유받은 PC 의 setup 이 이 묶음을 받는다`);
