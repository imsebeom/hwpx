#!/usr/bin/env node
/**
 * 이 PC 에서 빌드한 에디터(studio-dist, sdk)를 GitHub 릴리스로 올리고 prebuilt.json 을 갱신한다(관리자용).
 *   node setup.mjs --build   (원본을 고쳤으면 먼저 빌드)
 *   node release.mjs          → 릴리스 editor-<지문 12자> 를 저장소마다 만들고 zip 을 붙인다. 그 뒤 prebuilt.json 을 커밋, 푸시한다
 *   node release.mjs --prune  → 올리지 않고 오래된 묶음 정리만
 * 올린 뒤 저장소마다 editor-* 릴리스를 최근 KEEP 개만 남기고 지운다(태그도). 다른 릴리스는 건드리지 않는다.
 * 옛 커밋을 받은 PC 가 설치할 때 쓰도록 최신 하나만이 아니라 몇 개를 남긴다(2026-10-03 사용자 결정).
 * gh CLI 로그인이 필요하다. 저장소는 REPOS 에 적는다.
 */
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { MANIFEST, packDist, sourceHash } from './prebuilt.mjs';

const REPOS = ['imsebeom/hwpx', 'imsebeom/hwpx2'];
const KEEP = 3;
const HERE = path.dirname(MANIFEST);
const gh = (args) => spawnSync('gh', args, { encoding: 'utf8' });

function prune(repo) {
  const r = gh(['api', `repos/${repo}/releases`, '--paginate', '--jq', '.[] | select(.tag_name | startswith("editor-")) | "\\(.created_at) \\(.tag_name)"']);
  if (r.status !== 0) { console.error(`${repo}: 릴리스 목록 실패 ${r.stderr}`); return; }
  const tags = r.stdout.trim().split('\n').filter(Boolean).sort().reverse().map((l) => l.split(' ')[1]);
  for (const t of tags.slice(KEEP)) {
    const d = gh(['release', 'delete', t, '--yes', '--cleanup-tag', '--repo', repo]);
    console.log(d.status === 0 ? `${repo}: ${t} 지움` : `${repo}: ${t} 지우기 실패 ${d.stderr}`);
  }
}
if (process.argv.includes('--prune')) {
  for (const repo of REPOS) prune(repo);
  process.exit(0);
}
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

for (const repo of REPOS) {
  const notes = `hwpx 스킬 에디터 모드 미리 빌드 묶음(studio-dist, sdk). rhwp 0.8.6 + editor/patches 엔진 패치.\n원본 지문 ${hash}\nsetup.mjs 가 지문이 같으면 이것을 받아 쓴다(Rust 없이도 패치가 든 엔진).`;
  let r = gh(['release', 'view', tag, '--repo', repo]);
  r = r.status === 0
    ? gh(['release', 'upload', tag, file, '--clobber', '--repo', repo])
    : gh(['release', 'create', tag, file, '--repo', repo, '--title', `에디터 묶음 ${hash.slice(0, 12)}`, '--notes', notes, '--latest=false']);
  if (r.status !== 0) { console.error(`${repo}: ${r.stderr || r.stdout}`); process.exit(1); }
  console.log(`${repo}: ${tag}`);
  prune(repo);
}

const manifest = {
  sourceHash: hash, sha256, tag, asset, rhwp: '0.8.6', builtAt: new Date().toISOString(),
  urls: REPOS.map((repo) => `https://github.com/${repo}/releases/download/${tag}/${asset}`),
};
fs.writeFileSync(MANIFEST, JSON.stringify(manifest, null, 2) + '\n');
fs.unlinkSync(file);
console.log(`prebuilt.json 갱신 — 커밋, 푸시하면 공유받은 PC 의 setup 이 이 묶음을 받는다`);
