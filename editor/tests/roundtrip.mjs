// rhwp 로 열고 그대로 다시 저장한다(편집 없음). 에디터 모드 저장본의 보존력을 재는 시험.
//   node editor/tests/roundtrip.mjs <폴더>/*.hwpx   → 같은 폴더에 <이름>.rt.hwpx
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// RHWP_PKG 로 WASM 폴더를, RT_SUFFIX 로 출력 접미사를 바꿀 수 있다(빌드끼리 비교할 때).
const PKG = process.env.RHWP_PKG || path.join(path.dirname(fileURLToPath(import.meta.url)), '..', '.build', 'rhwp', 'pkg');
const SUFFIX = process.env.RT_SUFFIX || '.rt';
const { initSync, HwpDocument } = await import(new URL(`file:///${path.join(PKG, 'rhwp.js').replace(/\\/g, '/')}`).href);
initSync({ module: fs.readFileSync(path.join(PKG, 'rhwp_bg.wasm')) });

for (const f of process.argv.slice(2).filter((x) => !/\.(rt|base|patched)\./.test(x))) {
  try {
    const doc = new HwpDocument(new Uint8Array(fs.readFileSync(f)));
    const pages = doc.pageCount();
    const out = f.replace(/\.hwpx?$/, `${SUFFIX}.hwpx`);
    fs.writeFileSync(out, doc.exportHwpx());
    console.log(`${path.basename(f)}\trhwp쪽수=${pages}\t${fs.statSync(f).size}→${fs.statSync(out).size}B`);
  } catch (e) {
    console.log(`${path.basename(f)}\t실패: ${e?.message ?? e}`);
  }
}
