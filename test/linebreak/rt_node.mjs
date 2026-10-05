// 같은 엔진으로 폭 표 등록 없이, 등록하고 나서 같은 문단을 다시 나눠 본다: node rt_node.mjs <문서.hwpx>
import fs from 'node:fs';
const dir = 'C:/Users/hccga/.claude/skills/hwpx/editor/studio-dist/node';
const m = await import('file:///' + dir + '/rhwp.js');
m.initSync({ module: fs.readFileSync(dir + '/rhwp_bg.wasm') });
const { docFontMetrics, registerInto } = await import('file:///C:/Users/hccga/.claude/skills/hwpx/editor/font-metrics.mjs');
const bytes = fs.readFileSync(process.argv[2]);
const [ppi, ci, cell, cp] = [172, 0, 21, 1];
const rebreak = () => {
  const doc = new m.HwpDocument(new Uint8Array(bytes));
  doc.insertTextInCell(0, ppi, ci, cell, cp, 0, 'x');
  doc.deleteTextInCell(0, ppi, ci, cell, cp, 0, 1);
  const starts = [];
  for (let off = 0; off < 80; off++) {
    const s = JSON.parse(doc.getLineInfoInCell(0, ppi, ci, cell, cp, off)).charStart;
    if (starts[starts.length - 1] !== s) starts.push(s);
  }
  doc.free?.();
  return JSON.stringify(starts.slice(0, 3));
};
console.log('등록 없이 다시 나눔:', rebreak());
const fonts = docFontMetrics(bytes, m);
console.log('등록', registerInto(m, fonts.metrics), '개 얼굴:', fonts.read.join(', '));
console.log('등록 뒤 다시 나눔:', rebreak(), '(한/글 [0,49])');
