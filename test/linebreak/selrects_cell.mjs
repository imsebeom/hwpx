// 칸 문단의 선택 사각형을 찍는다: node selrects_cell.mjs <wasm폴더> <hwpx>
// 본문 문단마다 표를 찾아 첫 칸 첫 문단을 처음부터 끝까지 고른 사각형을 찍는다(여러 줄이면 줄마다 하나여야 한다).
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const [dir, file] = process.argv.slice(2);
const m = await import(pathToFileURL(path.join(dir, 'rhwp.js')).href);
m.initSync({ module: fs.readFileSync(path.join(dir, 'rhwp_bg.wasm')) });
const { docFontMetrics, registerInto } = await import(pathToFileURL('C:/Users/hccga/.claude/skills/hwpx/editor/font-metrics.mjs').href);
const bytes = fs.readFileSync(file);
registerInto(m, docFontMetrics(bytes, m).metrics);
const doc = new m.HwpDocument(bytes);
const n = doc.getParagraphCount(0);
for (let p = 0; p < n; p++) {
  for (let ci = 0; ci < 4; ci++) {
    for (let cell = 0; cell < 4; cell++) {
      let len;
      try { len = doc.getCellParagraphLength(0, p, ci, cell, 0); } catch { continue; }
      if (!len || len < 40) continue;
      const rects = JSON.parse(doc.getSelectionRectsInCell(0, p, ci, cell, 0, 0, 0, len));
      console.log(`문단 ${p} 개체 ${ci} 칸 ${cell} 길이 ${len}`);
      for (const r of rects) console.log(`  쪽 ${r.pageIndex} x ${r.x.toFixed(1)} y ${r.y.toFixed(1)} 폭 ${r.width.toFixed(1)}`);
      for (const off of [0, len]) {
        try {
          const c = JSON.parse(doc.getCursorRectInCell(0, p, ci, cell, 0, off));
          console.log(`  커서 ${off}: x ${c.x.toFixed(1)} y ${c.y.toFixed(1)}`);
        } catch (e) { console.log('  커서 실패', String(e).slice(0, 80)); }
      }
    }
  }
}
