/**
 * 큰 hwpx 의 그림 축소 보기(2026-09-29). 567MB 교재(그림 486장)는 서버가 문서를 base64 문자열 하나로
 * 보낼 수 없고(V8 문자열 상한 약 5.4억 자) 엔진 메모리도 3GB 가까이 쓴다. 그래서 그림만 줄인 사본을 연다.
 *
 * - makeProxy: image_proxy.py 로 사본과 대응표를 만든다. 원본 그림은 작업 공간의 proxy-orig.hwpx 사본에서 가져온다
 *   (화면 저장을 한 번 하면 원본 파일의 그림 이름이 rhwp 번호로 바뀌므로 원본 파일에서 찾으면 안 된다).
 * - restoreImages: 저장본에서 줄인 그림과 sha1 이 같은 것을 원본 바이트, 원래 확장자와 media-type 으로 되돌린다.
 *   rhwp 는 저장할 때 그림 id 를 새로 매기지만(image902 → image116) 바이트는 그대로 두므로 해시로 짝을 짓는다.
 *   사용자가 새로 넣은 그림은 해시가 달라 그대로 남는다.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { fileURLToPath } from 'node:url';
import { readZip, writeZip } from './hwpx-zip.mjs';

const execFileP = promisify(execFile);
const HERE = path.dirname(fileURLToPath(import.meta.url));

/** 그림 축소 보기를 켤 파일 크기(바이트). HWPX_EDITOR_PROXY_MB 로 바꾼다(0 이면 끔). */
export const PROXY_MIN_BYTES = Number(process.env.HWPX_EDITOR_PROXY_MB ?? 150) * 1e6;

/** buf(에디터에 보낼 판)의 그림을 줄인 사본. 원본 파일 크기와 수정 시각으로 캐시한다. 반환 { buf, map, images, beforeMB, afterMB, cached } */
export async function makeProxy(src, buf, stateDir) {
  const orig = path.join(stateDir, 'proxy-orig.hwpx');
  const out = path.join(stateDir, 'proxy.hwpx');
  const map = path.join(stateDir, 'proxy-map.json');
  const keyFile = path.join(stateDir, 'proxy-key.json');
  const st = fs.statSync(src);
  const key = JSON.stringify({ src, size: st.size, mtimeMs: st.mtimeMs, bytes: buf.length });
  try {
    if (fs.readFileSync(keyFile, 'utf8') === key && fs.existsSync(out) && fs.existsSync(orig)) {
      const m = JSON.parse(fs.readFileSync(map, 'utf8'));
      return { buf: fs.readFileSync(out), map, images: m.images.length, cached: true };
    }
  } catch { /* 캐시 없음 */ }
  fs.writeFileSync(orig, buf);
  const { stdout } = await execFileP('python', [path.join(HERE, 'image_proxy.py'), orig, out, map],
    { timeout: 600000, windowsHide: true, env: { ...process.env, PYTHONIOENCODING: 'utf-8' } });
  fs.writeFileSync(keyFile, key);
  return { buf: fs.readFileSync(out), map, ...JSON.parse(stdout.trim().split('\n').pop()), cached: false };
}

/** 저장본의 줄인 그림을 원본으로. 반환 { buf, restored, total } */
export function restoreImages(saved, mapFile) {
  const m = JSON.parse(fs.readFileSync(mapFile, 'utf8'));
  const bySha = new Map(m.images.map((i) => [i.sha1, i]));
  const entries = readZip(saved);
  const hits = [];
  for (const e of entries) {
    if (!e.name.startsWith('BinData/')) continue;
    const i = bySha.get(crypto.createHash('sha1').update(e.data).digest('hex'));
    if (i) hits.push([e, i]);
  }
  if (!hits.length) return { buf: saved, restored: 0, total: m.images.length };
  const want = new Set(hits.map(([, i]) => i.orig));
  const origs = new Map(readZip(fs.readFileSync(path.join(path.dirname(mapFile), 'proxy-orig.hwpx')), (n) => want.has(n)).map((e) => [e.name, e.data]));
  const hpfEntry = entries.find((e) => e.name === 'Contents/content.hpf');
  let hpf = hpfEntry.data.toString('utf8');
  let restored = 0;
  for (const [e, i] of hits) {
    const data = origs.get(i.orig);
    if (!data) continue;
    const name = e.name.replace(/\.[^./]+$/, '') + path.extname(i.orig);
    hpf = hpf.replace(new RegExp(`<opf:item [^>]*href="${e.name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}"[^>]*/>`), (item) => {
      let s = item.replace(`href="${e.name}"`, `href="${name}"`);
      if (i.mediaType) s = s.replace(/media-type="[^"]*"/, `media-type="${i.mediaType}"`);
      return s;
    });
    e.name = name;
    e.data = data;
    restored++;
  }
  hpfEntry.data = Buffer.from(hpf, 'utf8');
  return { buf: writeZip(entries), restored, total: m.images.length };
}
