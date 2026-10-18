/**
 * HWP(바이너리) → HWPX 를 에디터 엔진(스킬 패치가 든 WASM)으로 내보낸다.
 *
 *   node hwp_export_hwpx.mjs <in.hwp> <out.hwpx>
 *
 * 기본 변환은 rhwp CLI(scripts/rhwp_convert.py hwp_to_hwpx)다. CLI 0.8.6 은 .hwp 구역 끝 메모 목록(MEMO_LIST)을 읽지 않아
 * 메모 본문을 버린다(2026-10-19 사용자 보고). 스킬 엔진 패치 memo-list-body-text 가 그 목록을 읽으므로, 변환본에 본문 없는
 * 메모가 있으면 rhwp_convert.py 가 이 스크립트로 다시 내보낸다. 엔진 폴더는 RHWP_ENGINE, 없으면 studio-dist/node.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const [src, dst] = process.argv.slice(2);
if (!src || !dst) {
  console.error('사용: node hwp_export_hwpx.mjs <in.hwp> <out.hwpx>');
  process.exit(2);
}
const dir = process.env.RHWP_ENGINE || path.join(HERE, 'studio-dist', 'node');
const m = await import(pathToFileURL(path.join(dir, 'rhwp.js')).href);
m.initSync({ module: fs.readFileSync(path.join(dir, 'rhwp_bg.wasm')) });
const doc = new m.HwpDocument(fs.readFileSync(src));
fs.writeFileSync(dst, Buffer.from(doc.exportHwpx()));
