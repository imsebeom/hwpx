// 문서마다 쪽 수와 본문 문단별 쪽을 뽑는다: node pagemap.mjs <wasm폴더> <목록.txt> <출력.json>
// 에디터 서버처럼 엔진에 폭 표가 없는 글꼴은 설치된 글꼴 파일에서 읽어 등록한다(NO_FONT_FILES=1 이면 등록하지 않는다)
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
const [dir, list, out] = process.argv.slice(2);
const m = await import(pathToFileURL(path.join(dir, 'rhwp.js')).href);
m.initSync({ module: fs.readFileSync(path.join(dir, 'rhwp_bg.wasm')) });
const { docFontMetrics, registerInto } = await import(pathToFileURL('C:/Users/hccga/.claude/skills/hwpx/editor/font-metrics.mjs').href);
const res = {};
let registered = 0;
for (const line of fs.readFileSync(list, 'utf8').split(/\r?\n/).filter(Boolean)) {
  const [src, key = src] = line.split('\t');
  const f = key;
  try {
    const bytes = fs.readFileSync(src);
    if (!process.env.NO_FONT_FILES) registered += registerInto(m, docFontMetrics(bytes, m).metrics);
    const doc = new m.HwpDocument(bytes);
    const secs = [];
    for (let s = 0; s < 64; s++) {
      let n;
      try { n = doc.getParagraphCount(s); } catch { break; }
      const pg = [];
      for (let p = 0; p < n; p++) {
        let v;
        try { v = JSON.parse(doc.getPageOfPosition(s, p)).page; } catch { v = -1; }
        pg.push(v);
      }
      secs.push(pg);
    }
    res[f] = { pages: doc.pageCount(), secs };
    doc.free?.();
  } catch (e) {
    res[f] = { error: String(e).slice(0, 200) };
  }
}
fs.writeFileSync(out, JSON.stringify(res));
console.log('done', Object.keys(res).length, '글꼴 파일에서 등록한 얼굴', registered);
