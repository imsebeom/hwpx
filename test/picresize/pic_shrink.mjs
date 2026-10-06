// 표 속 표 칸의 그림을 엔진 API 로 줄인 뒤 그림 상자, 표 높이, 다음 문단 자리를 본다: node pic_shrink.mjs <hwpx>
import fs from 'node:fs';
const dir = 'C:/Users/hccga/.claude/skills/hwpx/editor/studio-dist/node';
const m = await import('file:///' + dir + '/rhwp.js');
m.initSync({ module: fs.readFileSync(dir + '/rhwp_bg.wasm') });
const doc = new m.HwpDocument(new Uint8Array(fs.readFileSync(process.argv[2])));
const layout = (p) => JSON.parse(doc.getPageControlLayout(p)).controls;
const pic = layout(1).find((c) => c.type === 'image');
console.log('그림(쪽 좌표)', JSON.stringify({ x: pic.x, y: pic.y, w: pic.w, h: pic.h, para: pic.paraIdx, ctrl: pic.controlIdx, stable: pic.stableIndex, cellPath: pic.cellPath ?? null }));
// 그림을 담은 칸 경로: stableIndex 가 [sec, para, ctrl, cell?, ...] 꼴로 보인다 — 플러그인이 쓰는 경로 형식으로 바꾼다
const si = pic.stableIndex;   // [0,3,0, 0,3,0, 0,0,0] = (sec,para,ctrl) 셋씩?
console.log('stableIndex', si);
const tables = layout(1).filter((c) => c.type === 'table').map((c) => ({ x: c.x, y: c.y, w: c.w, h: c.h, para: c.paraIdx, ctrl: c.controlIdx, depth: c.stableIndex.length / 3, stable: c.stableIndex }));
console.log('표(2쪽)', JSON.stringify(tables));
const path = JSON.stringify(pic.cellPath);
const nextPara = (cp) => JSON.stringify(pic.cellPath.map((h, i) => (i === pic.cellPath.length - 1 ? { ...h, cellParaIndex: cp } : h)));
const snap = (label) => {
  const l = layout(1);
  const p = l.find((c) => c.type === 'image');
  const t = l.find((c) => c.type === 'table' && c.stableIndex.length === 9 && c.paraIdx === 7);
  const props = JSON.parse(doc.getCellPicturePropertiesByPath(0, 3, path, 0));
  let next = null;
  for (const cp of [1, 2]) { try { next = JSON.parse(doc.getCursorRectByPath(0, 3, nextPara(cp), 0)); break; } catch { /* 없음 */ } }
  let cellText = '';
  for (let cp = 0; cp < 4; cp++) { try { cellText += `[${cp}]` + doc.getTextInCellByPath?.(0, 3, nextPara(cp), 0, 40) + ' '; } catch { break; } }
  console.log(label, '그림 모델', props.width, 'x', props.height, '| 그림 상자', p ? `${p.y}~${(p.y + p.h).toFixed(1)} h${p.h}` : '없음', '| 그래프 표', t ? `${t.y}~${(t.y + t.h).toFixed(1)} h${t.h}` : '없음', '| 다음 문단 캐럿 y', next ? next.y : '?', '| 쪽수', doc.pageCount());
};
snap('전 ');
const props = JSON.parse(doc.getCellPicturePropertiesByPath(0, 3, path, 0));
const r = doc.setCellPicturePropertiesByPath(0, 3, path, 0, JSON.stringify({ width: Math.round(props.width * 0.6), height: Math.round(props.height * 0.6) }));
console.log('줄임 결과', String(r).slice(0, 100));
snap('후 ');
