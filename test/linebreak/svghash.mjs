// 문서마다 쪽 SVG 의 해시를 뽑는다: node svghash.mjs <wasm폴더> <목록.txt> <출력.json>
// 두 엔진의 출력 json 을 견주면 칸 안 위치처럼 쪽 배치에 안 드러나는 변화도 잡힌다
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
const [dir, list, out] = process.argv.slice(2);
const m = await import(pathToFileURL(path.join(dir, 'rhwp.js')).href);
m.initSync({ module: fs.readFileSync(path.join(dir, 'rhwp_bg.wasm')) });
const { docFontMetrics, registerInto } = await import(pathToFileURL('C:/Users/hccga/.claude/skills/hwpx/editor/font-metrics.mjs').href);
const res = {};
for (const line of fs.readFileSync(list, 'utf8').split(/\r?\n/).filter(Boolean)) {
  const [src, key = src] = line.split('\t');
  try {
    const bytes = fs.readFileSync(src);
    registerInto(m, docFontMetrics(bytes, m).metrics);
    const doc = new m.HwpDocument(bytes);
    const pages = [];
    for (let p = 0; p < doc.pageCount(); p++) {
      pages.push(crypto.createHash('md5').update(doc.renderPageSvg(p)).digest('hex').slice(0, 12));
    }
    res[key] = pages;
    doc.free?.();
  } catch (e) {
    res[key] = { error: String(e).slice(0, 200) };
  }
}
fs.writeFileSync(out, JSON.stringify(res));
console.log('done', Object.keys(res).length);
