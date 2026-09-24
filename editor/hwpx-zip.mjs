/**
 * hwpx(zip) 읽기, 쓰기와 저장 단계 보정. 의존성 없음(Node 22+ 의 zlib.crc32 사용).
 *
 * fixHfFields: rhwp 0.8.6 은 머리말/꼬리말의 쪽 번호 필드를 텍스트 표식(\u0015 현재 쪽,
 * \u0016 총 쪽수)으로만 들고 있다가 hwpx 로 저장할 때 버린다. 저장 직전에 표식 위치를 받아
 * 한컴 형식의 <hp:autoNum> 컨트롤을 그 자리에 되살린다. rhwp 를 패치 빌드하면(setup.mjs)
 * 표식이 저장본에 이미 컨트롤로 들어가므로 이 보정은 할 일이 없다.
 */
import zlib from 'node:zlib';

/** [{ name, method, data(압축 해제된 Buffer) }] — 원래 순서 그대로. */
export function readZip(buf) {
  let eocd = buf.length - 22;
  while (eocd >= 0 && buf.readUInt32LE(eocd) !== 0x06054b50) eocd--;
  if (eocd < 0) return null;
  const out = [];
  let p = buf.readUInt32LE(eocd + 16);
  for (let i = buf.readUInt16LE(eocd + 10); i > 0; i--) {
    const method = buf.readUInt16LE(p + 10), size = buf.readUInt32LE(p + 20);
    const nameLen = buf.readUInt16LE(p + 28), extra = buf.readUInt16LE(p + 30), comment = buf.readUInt16LE(p + 32);
    const local = buf.readUInt32LE(p + 42);
    const name = buf.toString('utf8', p + 46, p + 46 + nameLen);
    const start = local + 30 + buf.readUInt16LE(local + 26) + buf.readUInt16LE(local + 28);
    const raw = buf.subarray(start, start + size);
    out.push({ name, method, data: method === 8 ? zlib.inflateRawSync(raw) : Buffer.from(raw) });
    p += 46 + nameLen + extra + comment;
  }
  return out;
}

/** readZip 결과를 다시 zip 으로. mimetype 처럼 무압축이던 항목은 무압축으로 둔다. */
export function writeZip(entries) {
  const locals = [], centrals = [];
  let offset = 0;
  for (const e of entries) {
    const name = Buffer.from(e.name, 'utf8');
    const body = e.method === 8 ? zlib.deflateRawSync(e.data) : e.data;
    const crc = zlib.crc32(e.data) >>> 0;
    const lh = Buffer.alloc(30);
    lh.writeUInt32LE(0x04034b50, 0); lh.writeUInt16LE(20, 4); lh.writeUInt16LE(0x0800, 6);   // UTF-8 이름
    lh.writeUInt16LE(e.method, 8); lh.writeUInt32LE(crc, 14);
    lh.writeUInt32LE(body.length, 18); lh.writeUInt32LE(e.data.length, 22); lh.writeUInt16LE(name.length, 26);
    const ch = Buffer.alloc(46);
    ch.writeUInt32LE(0x02014b50, 0); ch.writeUInt16LE(20, 4); ch.writeUInt16LE(20, 6); ch.writeUInt16LE(0x0800, 8);
    ch.writeUInt16LE(e.method, 10); ch.writeUInt32LE(crc, 16);
    ch.writeUInt32LE(body.length, 20); ch.writeUInt32LE(e.data.length, 24); ch.writeUInt16LE(name.length, 28);
    ch.writeUInt32LE(offset, 42);
    locals.push(lh, name, body);
    centrals.push(ch, name);
    offset += 30 + name.length + body.length;
  }
  const cd = Buffer.concat(centrals);
  const end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50, 0); end.writeUInt16LE(entries.length, 8); end.writeUInt16LE(entries.length, 10);
  end.writeUInt32LE(cd.length, 12); end.writeUInt32LE(offset, 16);
  return Buffer.concat([...locals, cd, end]);
}

const APPLY = ['BOTH', 'EVEN', 'ODD'];
const autoNum = (type) =>
  `<hp:ctrl><hp:autoNum num="1" numType="${type}"><hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar="" supscript="0"/></hp:autoNum></hp:ctrl>`;

/** 모델 텍스트에서 표식 위치를 "저장본에 남는 글자 수" 기준으로 뽑는다. */
function markerTargets(text) {
  const targets = [];
  let visible = 0;
  for (const c of text) {
    if (c === '\u0015' || c === '\u0016') targets.push({ at: visible, type: c === '\u0015' ? 'PAGE' : 'TOTAL_PAGE' });
    else if (c === '\t' || c === '\n' || c.charCodeAt(0) >= 0x20) visible++;
  }
  return targets;
}

/** 문단 XML 에서 글자 k 번째 앞 자리를 찾아 컨트롤을 끼운다. */
function insertAt(pXml, k, ctrl) {
  const re = /<hp:t\/>|<hp:t>|<\/hp:t>|<hp:(?:tab|lineBreak)\b[^>]*\/>|<[^>]+>|[^<]+/g;
  let inT = false, count = 0, lastTClose = -1, m;
  while ((m = re.exec(pXml))) {
    const tok = m[0];
    if (inT && count === k && tok !== '</hp:t>') return pXml.slice(0, m.index) + '</hp:t>' + ctrl + '<hp:t>' + pXml.slice(m.index);
    if (tok === '<hp:t>') inT = true;
    else if (tok === '</hp:t>') {
      if (count === k) return pXml.slice(0, m.index) + '</hp:t>' + ctrl + '<hp:t>' + pXml.slice(m.index);
      inT = false; lastTClose = m.index;
    } else if (inT && tok.startsWith('<hp:')) count++;
    else if (inT && !tok.startsWith('<')) {
      const chars = tok.match(/&[^;]+;|[\s\S]/gu);
      if (count + chars.length > k) {
        const idx = m.index + chars.slice(0, k - count).join('').length;
        return pXml.slice(0, idx) + '</hp:t>' + ctrl + '<hp:t>' + pXml.slice(idx);
      }
      count += chars.length;
    }
  }
  if (lastTClose >= 0) return pXml.slice(0, lastTClose) + '</hp:t>' + ctrl + '<hp:t>' + pXml.slice(lastTClose);
  // 글자가 하나도 없는 문단: 첫 run 안에 넣는다
  const selfRun = pXml.match(/<hp:run\b[^>]*\/>/);
  if (selfRun) return pXml.replace(selfRun[0], selfRun[0].replace(/\/>$/, '>') + ctrl + '</hp:run>');
  const openRun = pXml.match(/<hp:run\b[^>]*>/);
  if (openRun) return pXml.replace(openRun[0], openRun[0] + ctrl);
  return null;
}

/**
 * 스킬 파이프라인(hwpx_helpers.LINESEG_DUMMY, exam_builder)이 polaris-dvc 호환용으로 박는 한 줄짜리 더미 캐시.
 * 한글은 열 때 다시 계산하지만 rhwp 는 캐시를 믿어 문단 전체를 한 줄에 눌러 그린다(2026-09-25 실측).
 * 캐시가 없으면 rhwp 가 스스로 계산하므로 열기 전에 걷어낸다.
 */
const LINESEG_DUMMY = '<hp:linesegarray><hp:lineseg textpos="0" vertpos="0" vertsize="900" textheight="900" baseline="765" spacing="360" horzpos="0" horzsize="22960" flags="393216"/></hp:linesegarray>';

/** 반환: { buf, removed } — 더미가 없으면 원래 buf 그대로. */
export function stripDummyLinesegs(buf) {
  const entries = readZip(buf);
  if (!entries) return { buf, removed: 0 };
  let removed = 0;
  for (const e of entries) {
    if (!/^Contents\/section\d+\.xml$/.test(e.name)) continue;
    const xml = e.data.toString('utf8');
    const n = xml.split(LINESEG_DUMMY).length - 1;
    if (!n) continue;
    e.data = Buffer.from(xml.split(LINESEG_DUMMY).join(''), 'utf8');
    removed += n;
  }
  return removed ? { buf: writeZip(entries), removed } : { buf, removed: 0 };
}

/**
 * markers: [{ section, isHeader, applyTo, paras: [모델 텍스트, ...] }] (host.js save 가 모은다)
 * 반환: { buf, fixed, skipped: [사유] }
 */
export function fixHfFields(buf, markers) {
  const todo = markers.filter((m) => m.paras.some((t) => /[\u0015\u0016]/.test(t)));
  if (!todo.length) return { buf, fixed: 0, skipped: [] };
  const entries = readZip(buf);
  let fixed = 0;
  const skipped = [];
  for (const m of todo) {
    const kind = m.isHeader ? 'header' : 'footer';
    const entry = entries.find((e) => e.name === `Contents/section${m.section}.xml`);
    if (!entry) { skipped.push(`section${m.section}.xml 없음`); continue; }
    let xml = entry.data.toString('utf8');
    const elRe = new RegExp(`<hp:${kind}\\b[^>]*applyPageType="${APPLY[m.applyTo] ?? 'BOTH'}"[^>]*>[\\s\\S]*?</hp:${kind}>`);
    const el = xml.match(elRe);
    if (!el) { skipped.push(`${kind}(${APPLY[m.applyTo]}) 요소 없음`); continue; }
    const paras = el[0].match(/<hp:p\b[\s\S]*?<\/hp:p>/g) || [];
    if (paras.length !== m.paras.length || /<hp:tbl\b/.test(el[0])) {
      skipped.push(`${kind}(${APPLY[m.applyTo]}) 문단 수 불일치 또는 표 포함 — 보정 생략`);
      continue;
    }
    let newEl = el[0];
    paras.forEach((pXml, i) => {
      let out = pXml;
      const targets = markerTargets(m.paras[i]);
      // 패치 빌드 WASM 은 저장기가 이미 컨트롤을 냈다. 그 문단은 건드리지 않는다(쪽 번호 중복 방지).
      const already = (pXml.match(/numType="(?:PAGE|TOTAL_PAGE)"/g) || []).length;
      if (already >= targets.length) return;
      for (const t of targets.reverse()) {
        const next = insertAt(out, t.at, autoNum(t.type));
        if (next) { out = next; fixed++; } else skipped.push(`${kind} 문단 ${i} 삽입 자리 못 찾음`);
      }
      newEl = newEl.replace(pXml, out);
    });
    xml = xml.replace(el[0], newEl);
    entry.data = Buffer.from(xml, 'utf8');
  }
  return { buf: fixed ? writeZip(entries) : buf, fixed, skipped };
}
