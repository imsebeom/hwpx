/**
 * HWP(바이너리)를 rhwp 엔진으로 HWPX 로 바꾼다. 한글이 필요 없다.
 *
 *   node rhwp_hwp2hwpx.mjs <in.hwp> <out.hwpx>
 *
 * 엔진은 에디터가 쓰는 WASM 빌드(editor/studio-dist/node, setup.mjs 가 둔다)를 그대로 쓴다.
 * 공문 HWP 4건(그림, 표 포함)에서 한글 COM 변환본과 구조가 같고, 두 변환본을 한글 PDF 로 뽑으면
 * 픽셀까지 같았다(2026-10-02). 한글이 넣는 미리보기 PNG 만 빠져 파일이 조금 작다.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ENGINE = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'editor', 'studio-dist', 'node');
const [src, dst] = process.argv.slice(2);
if (!src || !dst) {
  console.error('사용: node rhwp_hwp2hwpx.mjs <in.hwp> <out.hwpx>');
  process.exit(2);
}
const m = await import(pathToFileURL(path.join(ENGINE, 'rhwp.js')).href);
m.initSync({ module: fs.readFileSync(path.join(ENGINE, 'rhwp_bg.wasm')) });
const doc = new m.HwpDocument(new Uint8Array(fs.readFileSync(src)));
fs.writeFileSync(dst, doc.exportHwpx());
console.log(`rhwp: ${path.basename(dst)} (${doc.pageCount()}쪽)`);
