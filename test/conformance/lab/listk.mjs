// mismatches.jsonl 의 list(목록 ID)를 칸 순번 k(nativescore, cellpara 번호)로 바꾼다.  node listk.mjs <id> <목록 ID>...
import fs from 'node:fs';
import { pathToFileURL } from 'node:url';
const ED = 'C:/Users/hccga/.claude/skills/hwpx/editor/';
const m = await import(pathToFileURL(ED + 'studio-dist/node/rhwp.js').href);
m.initSync({ module: fs.readFileSync(ED + 'studio-dist/node/rhwp_bg.wasm') });
const [id, ...ids] = process.argv.slice(2);
const es = fs.readFileSync(`out/oracle/${id}.hwpx`);
const cm = JSON.parse(new m.HwpDocument(es).getCursorModel());
const cells = cm.lists.filter((l) => l.isCell);
console.log(ids.map((x) => `${x}→${cells.findIndex((l) => l.listId === +x)}`).join(' '));
