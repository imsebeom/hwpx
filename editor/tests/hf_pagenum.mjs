// 머리말/꼬리말 쪽 번호가 hwpx 저장본에 컨트롤로 남는지 본다(저장 단계 보정 없이 WASM 만으로).
//   RHWP_PKG=<pkg 폴더> node editor/tests/hf_pagenum.mjs <입력.hwpx> <출력.hwpx>
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const PKG = process.env.RHWP_PKG || path.join(path.dirname(fileURLToPath(import.meta.url)), '..', '.build', 'rhwp', 'pkg');
const { initSync, HwpDocument } = await import(new URL(`file:///${path.join(PKG, 'rhwp.js').replace(/\\/g, '/')}`).href);
initSync({ module: fs.readFileSync(path.join(PKG, 'rhwp_bg.wasm')) });

const [src, out] = process.argv.slice(2);
const doc = new HwpDocument(new Uint8Array(fs.readFileSync(src)));
doc.applyHfTemplate(0, false, 0, 2);                 // 꼬리말 가운데 쪽 번호
doc.createHeaderFooter(0, true, 0);                  // 머리말 "전체 N쪽"
doc.insertTextInHeaderFooter(0, true, 0, 0, 0, '전체 쪽');
doc.insertFieldInHf(0, true, 0, 0, 3, 2);
fs.writeFileSync(out, doc.exportHwpx());
console.log(`${path.basename(out)} 저장, 쪽수 ${doc.pageCount()}`);
