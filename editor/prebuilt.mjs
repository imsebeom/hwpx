/**
 * 미리 빌드한 에디터(studio-dist, sdk)를 GitHub 릴리스로 주고받는다.
 *
 * 공유받은 PC 에는 Rust 가 없는 일이 많아, setup 이 npm 원본 WASM 을 써서 엔진 패치(patches/)가 모두 빠졌다.
 * 이 PC 에서 빌드한 묶음을 릴리스에 올려 두고, 원본 지문(patches, plugin, setup.mjs)이 같으면 그것을 받아 쓴다.
 *   올리기: node release.mjs          받기: setup.mjs 가 부른다(installPrebuilt)
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { readZip, writeZip } from './hwpx-zip.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const MANIFEST = path.join(HERE, 'prebuilt.json');
const PACKED = ['studio-dist', 'sdk'];

function walk(dir, base = dir, out = []) {
  if (!fs.existsSync(dir)) return out;
  for (const f of fs.readdirSync(dir).sort()) {
    const p = path.join(dir, f);
    if (/^(\.ruff_cache|__pycache__|node_modules)$/.test(f)) continue;
    if (fs.statSync(p).isDirectory()) walk(p, base, out);
    else out.push(path.relative(base, p).split(path.sep).join('/'));
  }
  return out;
}

/** 에디터 묶음을 만드는 원본의 지문. 줄바꿈은 LF 로 맞춘다(Windows git 이 CRLF 로 꺼내도 같게). */
export function sourceHash() {
  const h = crypto.createHash('sha256');
  const add = (rel) => {
    const buf = fs.readFileSync(path.join(HERE, rel));
    h.update(rel + '\0');
    h.update(/\.(rs|ts|js|mjs|json|md|css|html)$/.test(rel) ? Buffer.from(buf.toString('utf8').replace(/\r\n/g, '\n')) : buf);
  };
  add('setup.mjs');
  for (const d of ['patches', 'plugin']) for (const rel of walk(path.join(HERE, d))) add(`${d}/${rel}`);
  return h.digest('hex');
}

/** studio-dist, sdk 를 zip 하나로. */
export function packDist() {
  const entries = [];
  for (const d of PACKED) {
    for (const rel of walk(path.join(HERE, d))) {
      const data = fs.readFileSync(path.join(HERE, d, rel));
      entries.push({ name: `${d}/${rel}`, method: /\.(png|jpe?g|gif|woff2?)$/i.test(rel) ? 0 : 8, data });
    }
  }
  return writeZip(entries);
}

/**
 * 지문이 맞는 미리 빌드한 묶음이 있으면 받아서 풀고 true. 없거나 실패하면 false(호출자가 빌드한다).
 * 이미 같은 지문으로 풀어 둔 studio-dist 가 있으면 받지 않는다.
 */
export async function installPrebuilt(log = console.log) {
  if (!fs.existsSync(MANIFEST)) return false;
  const m = JSON.parse(fs.readFileSync(MANIFEST, 'utf8'));
  const hash = sourceHash();
  const stamp = path.join(HERE, 'studio-dist', '.source-hash');
  // 이 PC 가 직접 빌드한 것(hash)이나 이미 받은 묶음(m.sourceHash)이 있으면 그대로 쓴다
  const have = fs.existsSync(stamp) ? fs.readFileSync(stamp, 'utf8').trim() : '';
  if (have === hash || have === m.sourceHash) { log('에디터가 이미 설치돼 있다'); return true; }
  // 원본이 묶음보다 새로워도(관리자가 release 를 빠뜨린 경우) 빌드하지 않고 지난 묶음을 쓴다 — 공유받은 PC 에서 빌드는 10분이 넘는다
  if (m.sourceHash !== hash) log(`⚠ 미리 빌드한 에디터가 원본보다 오래됐다(${m.sourceHash.slice(0, 12)} ≠ ${hash.slice(0, 12)}) — 지난 묶음을 쓴다. 최신 원본으로 쓰려면 setup.mjs --build`);
  const tries = [];
  for (const url of m.urls) for (const wait of [0, 3000, 10000]) tries.push([url, wait]);   // 릴리스 직후 등 일시 실패에 대비해 주소마다 세 번
  for (const [url, wait] of tries) {
    try {
      if (wait) await new Promise((r) => setTimeout(r, wait));
      log(`미리 빌드한 에디터 받기: ${url}`);
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const buf = Buffer.from(await res.arrayBuffer());
      const sha = crypto.createHash('sha256').update(buf).digest('hex');
      if (sha !== m.sha256) throw new Error(`sha256 이 다르다(${sha.slice(0, 12)})`);
      const entries = readZip(buf);
      if (!entries?.length) throw new Error('zip 을 못 읽었다');
      for (const d of PACKED) rmrfSafe(path.join(HERE, d));
      for (const e of entries) {
        const out = path.join(HERE, ...e.name.split('/'));
        if (!out.startsWith(HERE + path.sep)) throw new Error(`zip 안의 이상한 경로: ${e.name}`);
        fs.mkdirSync(path.dirname(out), { recursive: true });
        fs.writeFileSync(out, e.data);
      }
      fs.writeFileSync(stamp, m.sourceHash);
      log(`풀었다: 파일 ${entries.length}개, ${(buf.length / 1048576).toFixed(1)} MB`);
      return true;
    } catch (e) {
      log(`  실패: ${e.message}`);
    }
  }
  return false;
}

// Node 24 의 fs.rmSync(recursive)는 한글 경로에서 node 를 죽인다 — 한 단계씩 지운다(setup.mjs 와 같은 이유)
function rmrfSafe(p) {
  if (!fs.existsSync(p)) return;
  if (fs.lstatSync(p).isDirectory()) {
    for (const f of fs.readdirSync(p)) rmrfSafe(path.join(p, f));
    fs.rmdirSync(p);
  } else fs.unlinkSync(p);
}
