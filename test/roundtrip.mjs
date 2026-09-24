// rhwp 로 열고 그대로 다시 저장한다(편집 없음). 에디터 모드 저장본의 보존력을 재는 시험.
//   node test/roundtrip.mjs test/rt/*.hwpx   → 같은 폴더에 <이름>.rt.hwpx
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const PKG = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'editor', '.build', 'rhwp', 'pkg');
const { initSync, HwpDocument } = await import(new URL(`file:///${path.join(PKG, 'rhwp.js').replace(/\\/g, '/')}`).href);
initSync({ module: fs.readFileSync(path.join(PKG, 'rhwp_bg.wasm')) });

for (const f of process.argv.slice(2).filter((x) => !x.includes('.rt.'))) {
  try {
    const doc = new HwpDocument(new Uint8Array(fs.readFileSync(f)));
    const pages = doc.pageCount();
    const out = f.replace(/\.hwpx?$/, '.rt.hwpx');
    fs.writeFileSync(out, doc.exportHwpx());
    console.log(`${path.basename(f)}\trhwp쪽수=${pages}\t${fs.statSync(f).size}→${fs.statSync(out).size}B`);
  } catch (e) {
    console.log(`${path.basename(f)}\t실패: ${e?.message ?? e}`);
  }
}
