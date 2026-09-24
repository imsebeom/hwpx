// @rhwp/core 의 HwpDocument 위에서 AI 가 부르는 편집 도구.
// 브라우저, Node, 스튜디오 플러그인(ai-edit) 세 곳에서 쓰도록 core 인스턴스만 받는다.
//
// 좌표 규칙: 문단은 구역(section) 안의 번호(p0, p1 …), 표는 문서 순서대로 T1, T2 …, 셀은 T1r2c1.
// 문단을 넣거나 지우면 뒤쪽 번호가 밀리므로 도구 결과에 그 사실을 적어 돌려준다.

const J = (s) => (typeof s === 'string' ? JSON.parse(s) : s);

function paraText(doc, s, p) {
  const len = doc.getParagraphLength(s, p);
  return len ? doc.getTextRange(s, p, 0, len) : '';
}

/**
 * 본문의 표만 T1, T2 … 로 매긴다. getControls() 는 셀 안의 표도 돌려주는데 그때 list 는 구역 번호가 아닌
 * 셀 리스트 id 다(실측: 안쪽 표가 list:2). 본문 표는 list 가 구역 번호이고 그 문단에 표 컨트롤이 있다.
 */
export function listTables(doc) {
  const secCount = doc.getSectionCount();
  return J(doc.getControls())
    .filter((c) => c.ctrlId === 'tbl' && c.list < secCount && c.para < doc.getParagraphCount(c.list) && isBodyTable(doc, c))
    .map((c, i) => ({ id: `T${i + 1}`, section: c.list, para: c.para, ctrl: c.controlIndex }));
}

function isBodyTable(doc, c) {
  try {
    J(doc.getTableDimensions(c.list, c.para, c.controlIndex));
    return true;
  } catch {
    return false;
  }
}

/** 셀 안에 든 표의 수. 개요에는 보이지 않으므로 따로 알린다. */
function nestedTableCount(doc) {
  return J(doc.getControls()).filter((c) => c.ctrlId === 'tbl').length - listTables(doc).length;
}

function findTable(doc, id) {
  const key = String(id).toUpperCase().replace(/^(\d+)$/, 'T$1');
  const all = listTables(doc);
  const t = all.find((x) => x.id === key);
  if (!t) throw new Error(`표 ${id} 가 없습니다. 이 문서의 표는 ${all.length ? `T1~T${all.length}` : '하나도 없습니다'}.`);
  return t;
}

function cellParaText(doc, t, c, i) {
  const len = doc.getCellParagraphLength(t.section, t.para, t.ctrl, c, i);
  return len ? doc.getTextInCell(t.section, t.para, t.ctrl, c, i, 0, len) : '';
}

function cellText(doc, t, c) {
  const n = doc.getCellParagraphCount(t.section, t.para, t.ctrl, c);
  const out = [];
  for (let i = 0; i < n; i++) out.push(cellParaText(doc, t, c, i));
  return out.join('\n');
}

function tableCells(doc, t) {
  const dim = J(doc.getTableDimensions(t.section, t.para, t.ctrl));
  const cells = [];
  for (let c = 0; c < dim.cellCount; c++) cells.push({ idx: c, ...J(doc.getCellInfo(t.section, t.para, t.ctrl, c)) });
  return { dim, cells };
}

function findCell(doc, t, row, col) {
  const { dim, cells } = tableCells(doc, t);
  const hit = cells.find((c) => row >= c.row && row < c.row + c.rowSpan && col >= c.col && col < c.col + c.colSpan);
  if (!hit) throw new Error(`${t.id} 에 r${row}c${col} 셀이 없습니다(${dim.rowCount}행×${dim.colCount}열, r0~r${dim.rowCount - 1}, c0~c${dim.colCount - 1}).`);
  return hit.idx;
}

function styleName(doc, s, p) {
  try {
    return J(doc.getStyleAt(s, p)).name;
  } catch {
    return '';
  }
}
const PLAIN_STYLES = new Set(['바탕글', '본문', 'Normal', 'Body', '']);

// ── 글 정리 ─────────────────────────────────────────

/** 모델이 넣은 마크다운 기호를 걷어낸다. 한글 문서에서는 그대로 글자로 박힌다. */
export function clean(text) {
  return String(text ?? '')
    .replace(/\*\*([^*\n]+)\*\*/g, '$1')
    .replace(/__([^_\n]+)__/g, '$1')
    .replace(/`([^`\n]+)`/g, '$1')
    .replace(/\[([^\]\n]+)\]\((?:https?:[^)]+|(?:s\d+)?p\d+|T\d+r\d+c\d+)\)/g, '$1')
    .replace(/^#{1,6}\s+/gm, '');
}

// 문단 앞 글머리 기호(□ ○ - ※, 1. 가. 1) 가) ① ㉮ 등). 고쳐 쓸 때 원문의 기호를 지킨다.
const BULLET = /^(\s*(?:[□■○●◦▪•◆◇▶▷※❍❏☐]|[-–―]|\(?\d{1,2}[.)]|\(?[가-하][.)]|[①-⑳㉠-㉭㉮-㉻])\s*)/;

export function keepBullet(original, next) {
  const m = original.match(BULLET);
  if (!m) return next;
  return m[1] + next.replace(BULLET, '').trimStart();
}

// ── 좌표 ───────────────────────────────────────────

/**
 * 링크 표기(p12, s1p3, T1r2c1)를 스튜디오 커서 위치로 바꾼다. 문단이면 전체 길이도 준다.
 * 답변 링크와 교정 부호를 눌러 편집기로 이동할 때 쓴다.
 */
export function resolveTarget(doc, ref) {
  const m = String(ref).replace(/\s+/g, '').match(/^(?:s(\d+))?p(\d+)$|^T(\d+)r(\d+)c(\d+)$/i);
  if (!m) return null;
  if (m[2] != null) {
    const s = Number(m[1] ?? 0);
    const p = Number(m[2]);
    if (p >= doc.getParagraphCount(s)) return null;
    return { sectionIndex: s, paragraphIndex: p, charOffset: 0, length: doc.getParagraphLength(s, p) };
  }
  const t = findTable(doc, `T${m[3]}`);
  const c = findCell(doc, t, Number(m[4]), Number(m[5]));
  return {
    sectionIndex: t.section, paragraphIndex: t.para, charOffset: 0,
    parentParaIndex: t.para, controlIndex: t.ctrl, cellIndex: c, cellParaIndex: 0,
    length: doc.getCellParagraphLength(t.section, t.para, t.ctrl, c, 0),
  };
}

/**
 * 서식 도구의 대상 표기를 펼친다. p5, p5-p9, T1r2c1, T1r0(행 전체), T1c0(열 전체), T1(표 전체).
 * 반환: [{kind:'para', s, p} | {kind:'cell', t, c}]
 */
function expandTargets(doc, at, section = 0) {
  const out = [];
  for (const raw of [].concat(at)) {
    const ref = String(raw).replace(/\s+/g, '');
    let m;
    if ((m = ref.match(/^p(\d+)(?:[-~]p?(\d+))?$/i))) {
      const from = Number(m[1]);
      const to = Number(m[2] ?? m[1]);
      for (let p = from; p <= to; p++) {
        checkPara(doc, section, p);
        out.push({ kind: 'para', s: section, p });
      }
    } else if ((m = ref.match(/^T(\d+)(?:r(\d+))?(?:c(\d+))?$/i))) {
      const t = findTable(doc, `T${m[1]}`);
      const [r, c] = [m[2], m[3]].map((x) => (x == null ? null : Number(x)));
      if (r != null && c != null) {
        out.push({ kind: 'cell', t, c: findCell(doc, t, r, c) });
      } else {
        const { cells } = tableCells(doc, t);
        const hit = cells.filter((x) => (r == null || x.row === r) && (c == null || x.col === c));
        if (!hit.length) throw new Error(`${ref} 에 해당하는 셀이 없습니다.`);
        for (const x of hit) out.push({ kind: 'cell', t, c: x.idx });
      }
    } else {
      throw new Error(`대상 표기 ${raw} 를 알 수 없습니다. p5, p5-p9, T1r2c1, T1r0, T1c0, T1 형식을 쓰세요.`);
    }
  }
  return out;
}

/** 대상 안에서 글자 범위를 찾는다. find 가 없으면 전체. 반환: [{i(셀 문단 또는 -1), start, end}] */
function rangesIn(doc, target, find) {
  const texts = target.kind === 'para'
    ? [[-1, paraText(doc, target.s, target.p)]]
    : Array.from({ length: doc.getCellParagraphCount(target.t.section, target.t.para, target.t.ctrl, target.c) },
      (_, i) => [i, cellParaText(doc, target.t, target.c, i)]);
  const out = [];
  for (const [i, text] of texts) {
    if (!find) {
      if (text.length) out.push({ i, start: 0, end: text.length });
      continue;
    }
    for (let k = text.indexOf(find); k >= 0; k = text.indexOf(find, k + find.length)) out.push({ i, start: k, end: k + find.length });
  }
  return out;
}

// ── 읽기 ─────────────────────────────────────────────

/**
 * 문서 개요. 문단 번호와 표 좌표, 스타일이 바탕글이 아닌 문단은 〈스타일〉을 붙인다.
 * opts.from/opts.to 로 문단 범위를 줄일 수 있다(구역 0 기준).
 */
export function outline(doc, opts = {}) {
  const secCount = doc.getSectionCount();
  const tables = listTables(doc);
  const lines = [];
  for (let s = 0; s < secCount; s++) {
    const n = doc.getParagraphCount(s);
    const from = s === 0 ? Math.max(0, opts.from ?? 0) : 0;
    const to = s === 0 ? Math.min(n - 1, opts.to ?? n - 1) : n - 1;
    for (let p = from; p <= to; p++) {
      const id = secCount > 1 ? `s${s}p${p}` : `p${p}`;
      const text = paraText(doc, s, p);
      const here = tables.filter((t) => t.section === s && t.para === p);
      const st = styleName(doc, s, p);
      const tag = PLAIN_STYLES.has(st) ? '' : ` 〈${st}〉`;
      lines.push(`${id}${tag}: ${text || (here.length ? '' : '(빈 문단)')}${here.map((t) => ` [${t.id}]`).join('')}`);
      for (const t of here) {
        const { dim, cells } = tableCells(doc, t);
        lines.push(`  ${t.id} 표 ${dim.rowCount}행×${dim.colCount}열`);
        for (let r = 0; r < dim.rowCount; r++) {
          const row = cells.filter((c) => c.row === r).map((c) => {
            const span = c.rowSpan > 1 || c.colSpan > 1 ? `(병합 ${c.rowSpan}×${c.colSpan})` : '';
            return `c${c.col}${span}「${cellText(doc, t, c.idx).replace(/\n/g, '⏎')}」`;
          });
          lines.push(`  ${t.id} r${r}: ${row.join(' ')}`);
        }
      }
    }
  }
  // getFieldList() 는 누름틀과 메모를 함께 돌려준다(메모는 fieldType:"memo", 이름 없음).
  const fields = J(doc.getFieldList());
  const clickHere = fields.filter((f) => f.fieldType !== 'memo');
  const memos = fields.filter((f) => f.fieldType === 'memo');
  if (clickHere.length) lines.push(`필드(누름틀): ${clickHere.map((f) => f.name || '(이름 없음)').join(', ')}`);
  if (memos.length) lines.push(`(메모가 ${memos.map((m) => `p${m.location?.paraIndex}`).join(', ')} 에 달려 있다. 편집해도 메모는 남는다.)`);
  for (const [isHeader, label] of [[true, '머리말'], [false, '꼬리말']]) {
    try {
      const hf = J(doc.getHeaderFooter(0, isHeader, 0));
      if (hf.exists) lines.push(`${label}: 「${hf.text}」`);
    } catch { /* 없음 */ }
  }
  const nested = nestedTableCount(doc);
  if (nested) lines.push(`(표 셀 안에 표가 ${nested}개 있다. 안쪽 표의 글은 개요에 보이지 않는다. 그 셀을 set_cell 로 바꾸면 바깥 셀의 글만 바뀌고 안쪽 표는 남는다. 안쪽 표의 글은 search_text 로 찾아 find_replace 로 고쳐라.)`);
  lines.push(`(전체 ${doc.pageCount()}쪽)`);
  return lines.join('\n');
}

/** 대화에 붙일 개요. 너무 길면 줄을 자르고, 그래도 길면 앞부분만 주고 범위 읽기를 안내한다. */
export function outlineForPrompt(doc, maxChars = 16000) {
  let text = outline(doc);
  if (text.length <= maxChars) return text;
  text = text.split('\n').map((l) => (l.length > 90 ? `${l.slice(0, 90)}…` : l)).join('\n');
  if (text.length <= maxChars) return `${text}\n(긴 줄은 잘렸다. 원문이 필요하면 read_document 에 from_para, to_para 를 주어 읽어라.)`;
  const cut = text.slice(0, maxChars);
  const lastPara = [...cut.matchAll(/^p(\d+)/gm)].pop()?.[1] ?? '0';
  return `${cut.slice(0, cut.lastIndexOf('\n'))}\n(p${lastPara} 이후는 생략했다. read_document 에 from_para, to_para 를 주어 나눠 읽어라.)`;
}

// ── 쓰기 헬퍼 ────────────────────────────────────────

function setCellText(doc, t, c, text) {
  const { section: s, para: p, ctrl: k } = t;
  for (let i = doc.getCellParagraphCount(s, p, k, c) - 1; i >= 1; i--) doc.mergeParagraphInCell(s, p, k, c, i);
  const len = doc.getCellParagraphLength(s, p, k, c, 0);
  if (len) doc.deleteTextInCell(s, p, k, c, 0, 0, len);
  String(text).split('\n').forEach((line, i) => {
    if (i > 0) doc.splitParagraphInCell(s, p, k, c, i - 1, doc.getCellParagraphLength(s, p, k, c, i - 1));
    if (line) doc.insertTextInCell(s, p, k, c, i, 0, line);
  });
}

// ── 안내 문구 서식 ────────────────────────────────────
// 서식 양식의 안내 문구는 흔히 빨간(또는 파란, 회색) 작은 글씨다. 그 자리에 글을 채우면 안내 서식을
// 물려받아 채운 내용이 안내처럼 보인다(한컴 실측: 빨간 8pt). 원문 첫 글자가 검지 않은 색이면 채운 뒤
// 검은색과 이웃 본문 크기로 돌린다.

const isGuideColor = (c) => !!c && !['#000000', '#ffffff'].includes(String(c).toLowerCase());

function cellCharAt(doc, t, c) {
  try {
    return J(doc.getCellCharPropertiesAt(t.section, t.para, t.ctrl, c, 0, 0));
  } catch {
    return null;
  }
}

/** set_cell 전에 부른다. 안내 서식이면 채운 뒤 입힐 본문 서식을 돌려준다. */
function plainStyleForCell(doc, t, c) {
  const p = cellCharAt(doc, t, c);
  if (!p || !isGuideColor(p.textColor) || !cellText(doc, t, c).trim()) return null;
  // 같은 행 왼쪽 라벨 칸의 크기를 쓴다. 없으면 10pt.
  const info = J(doc.getCellInfo(t.section, t.para, t.ctrl, c));
  let size = 1000;
  if (info.col > 0) size = cellCharAt(doc, t, findCell(doc, t, info.row, info.col - 1))?.fontSize ?? 1000;
  return { from: p, props: { textColor: '#000000', fontSize: size, italic: false } };
}

function plainStyleForPara(doc, s, p) {
  if (!doc.getParagraphLength(s, p)) return null;
  const cur = J(doc.getCharPropertiesAt(s, p, 0));
  if (!isGuideColor(cur.textColor)) return null;
  let size = 1000;
  for (let q = p - 1; q >= 0; q--) {
    if (!doc.getParagraphLength(s, q)) continue;
    const prev = J(doc.getCharPropertiesAt(s, q, 0));
    if (!isGuideColor(prev.textColor)) { size = prev.fontSize; break; }
  }
  return { from: cur, props: { textColor: '#000000', fontSize: size, italic: false } };
}

function applyPlainToCell(doc, t, c, plain) {
  const n = doc.getCellParagraphCount(t.section, t.para, t.ctrl, c);
  for (let i = 0; i < n; i++) {
    const len = doc.getCellParagraphLength(t.section, t.para, t.ctrl, c, i);
    if (len) doc.applyCharFormatInCell(t.section, t.para, t.ctrl, c, i, 0, len, JSON.stringify(plain.props));
  }
}

const plainNote = (plain) => `안내 문구 서식(${plain.from.textColor} ${plain.from.fontSize / 100}pt)을 본문 서식(검은색 ${plain.props.fontSize / 100}pt)으로 바꿨습니다. 원래 서식을 두려면 keep_style=true.`;

function insertParas(doc, s, after, texts) {
  texts.forEach((text, i) => {
    doc.insertParagraph(s, after + 1 + i);
    if (text) doc.insertText(s, after + 1 + i, 0, text);
  });
}

function checkPara(doc, s, p) {
  const n = doc.getParagraphCount(s);
  if (!(Number.isInteger(p) && p >= 0 && p < n)) throw new Error(`p${p} 는 범위 밖입니다(이 구역의 문단은 p0~p${n - 1}).`);
}

const shifted = (n, from) => `p${from} 뒤의 문단 번호가 ${n > 0 ? '+' : ''}${n} 만큼 바뀌었습니다. 이어서 편집하려면 새 번호를 쓰세요.`;

function charProps(a) {
  const props = {};
  for (const k of ['bold', 'italic', 'underline', 'strikethrough']) if (typeof a[k] === 'boolean') props[k] = a[k];
  if (a.size_pt != null) {
    const pt = Number(a.size_pt);
    if (!(pt >= 4 && pt <= 100)) throw new Error('size_pt 는 4~100 사이의 pt 값입니다(예: 12).');
    props.fontSize = Math.round(pt * 100);
  }
  if (a.color) {
    if (!/^#[0-9a-f]{6}$/i.test(a.color)) throw new Error('color 는 #RRGGBB 형식입니다.');
    props.textColor = a.color.toLowerCase();
  }
  if (!Object.keys(props).length) throw new Error('바꿀 서식이 없습니다(bold, italic, underline, strikethrough, size_pt, color).');
  return props;
}

const ALIGN = { left: 'left', center: 'center', right: 'right', justify: 'justify', distribute: 'distribute', 왼쪽: 'left', 가운데: 'center', 오른쪽: 'right', 양쪽: 'justify', 배분: 'distribute' };

function paraProps(a) {
  const props = {};
  if (a.align) {
    if (!ALIGN[a.align]) throw new Error('align 은 left, center, right, justify, distribute 중 하나입니다.');
    props.alignment = ALIGN[a.align];
  }
  if (a.line_spacing != null) {
    props.lineSpacing = Number(a.line_spacing);
    props.lineSpacingType = 'Percent';
  }
  const pt = { indent_pt: 'indent', left_margin_pt: 'marginLeft', space_before_pt: 'spacingBefore', space_after_pt: 'spacingAfter' };
  for (const [k, v] of Object.entries(pt)) if (a[k] != null) props[v] = Number(a[k]);
  if (typeof a.keep_with_next === 'boolean') props.keepWithNext = a.keep_with_next;
  if (typeof a.page_break_before === 'boolean') props.pageBreakBefore = a.page_break_before;
  if (!Object.keys(props).length) throw new Error('바꿀 문단 서식이 없습니다.');
  return props;
}

const PAGE_BREAK = { split: 2, cell: 1, none: 0 };
const norm = (s) => String(s).replace(/\s+/g, '');

// ── 도구 정의 ────────────────────────────────────────

const S = { section: { type: 'integer', description: '구역 번호. 구역이 하나면 생략(0)' } };
const AT = { type: 'string', description: '대상: p5, p5-p9, T1r2c1(셀), T1r0(행 전체), T1c0(열 전체), T1(표 전체)' };

export const TOOLS = [
  {
    name: 'read_document',
    description: '문서를 문단 번호(p0 …)와 표 좌표(T1 r0: c0「…」)로 다시 읽는다. from_para, to_para 로 범위를 줄일 수 있다. 문단을 넣거나 지운 뒤 번호를 확인할 때 쓴다.',
    parameters: { type: 'object', properties: { from_para: { type: 'integer' }, to_para: { type: 'integer' } } },
  },
  {
    name: 'search_text',
    description: '문서 전체(표 셀 포함)에서 글자열을 찾아 위치(p12, T1r2c1)와 앞뒤 문맥을 돌려준다. 고치기 전에 위치를 확인할 때 쓴다.',
    parameters: { type: 'object', properties: { query: { type: 'string' }, case_sensitive: { type: 'boolean' } }, required: ['query'] },
  },
  {
    name: 'replace_paragraph',
    description: '문단 하나의 글 전체를 새 글로 바꾼다. 문단 서식은 유지된다. 원문 앞의 글머리 기호(□ ○ - 1. 가. 등)는 자동으로 지켜진다(keep_bullet=false 로 끌 수 있다). text 에 줄바꿈이 있으면 둘째 줄부터 뒤에 새 문단으로 들어간다.',
    parameters: { type: 'object', properties: { ...S, para: { type: 'integer' }, text: { type: 'string' }, keep_bullet: { type: 'boolean' }, keep_style: { type: 'boolean', description: '안내 문구(빨간 글씨 등) 자리에 쓸 때 원래 서식을 유지. 기본은 검은 본문 서식으로 돌림' } }, required: ['para', 'text'] },
  },
  {
    name: 'insert_paragraphs',
    description: 'after_para 문단 바로 뒤에 새 문단들을 차례로 넣는다. 새 문단은 앞 문단의 서식과 스타일을 따르므로, 제목 문단 뒤보다 같은 종류의 본문 문단 뒤에 넣는 편이 낫다.',
    parameters: { type: 'object', properties: { ...S, after_para: { type: 'integer' }, texts: { type: 'array', items: { type: 'string' } } }, required: ['after_para', 'texts'] },
  },
  {
    name: 'delete_paragraphs',
    description: 'from_para 부터 to_para 까지(포함) 문단을 지운다. 표가 든 문단과 구역 첫 문단(p0)은 지울 수 없다.',
    parameters: { type: 'object', properties: { ...S, from_para: { type: 'integer' }, to_para: { type: 'integer' } }, required: ['from_para', 'to_para'] },
  },
  {
    name: 'find_replace',
    description: '문서 전체(표 안 포함)에서 글자열을 모두 찾아 바꾼다. 서식은 유지된다. 같은 글자열이 여러 곳에 있을 수 있으면 expected_count 로 기대 개수를 주어라(다르면 바꾸지 않고 위치를 알려 준다). 「성명:      (인)」처럼 공백으로 폭을 맞춘 칸은 keep_width=true 로 원래 글자 수를 유지한다.',
    parameters: { type: 'object', properties: { find: { type: 'string' }, replace: { type: 'string' }, expected_count: { type: 'integer' }, keep_width: { type: 'boolean' } }, required: ['find', 'replace'] },
  },
  {
    name: 'set_cell',
    description: '표 셀의 내용을 통째로 바꾼다. 줄바꿈은 셀 안 새 문단이 된다. 병합 셀은 그 영역 안의 아무 행과 열로 가리키면 된다.',
    parameters: { type: 'object', properties: { table: { type: 'string', description: 'T1 형식' }, row: { type: 'integer' }, col: { type: 'integer' }, text: { type: 'string' }, keep_style: { type: 'boolean', description: '안내 문구(빨간 글씨 등) 자리에 쓸 때 원래 서식을 유지. 기본은 검은 본문 서식으로 돌림' } }, required: ['table', 'row', 'col', 'text'] },
  },
  {
    name: 'fill_by_label',
    description: '표에서 라벨 칸(예: 「담당 부서」)을 찾아 그 오른쪽(또는 아래) 칸에 글을 넣는다. 좌표를 모를 때 양식 채우기에 쓴다. 같은 라벨이 여럿이면 후보 위치를 알려 주니 occurrence(1부터)로 고른다.',
    parameters: { type: 'object', properties: { label: { type: 'string' }, text: { type: 'string' }, direction: { type: 'string', enum: ['right', 'below'] }, occurrence: { type: 'integer' }, keep_style: { type: 'boolean', description: '안내 문구(빨간 글씨 등) 자리에 쓸 때 원래 서식을 유지. 기본은 검은 본문 서식으로 돌림' } }, required: ['label', 'text'] },
  },
  {
    name: 'format_text',
    description: '글자 서식을 바꾼다. at 의 문단이나 셀에서 text 에 해당하는 글자만(생략하면 전체) 굵게, 기울임, 밑줄, 취소선, 크기(pt), 색을 바꾼다. 지정하지 않은 속성은 그대로다.',
    parameters: {
      type: 'object',
      properties: {
        ...S, at: AT, text: { type: 'string', description: '이 글자열만 바꿈. 생략하면 대상 전체' },
        bold: { type: 'boolean' }, italic: { type: 'boolean' }, underline: { type: 'boolean' }, strikethrough: { type: 'boolean' },
        size_pt: { type: 'number', description: '글자 크기 pt(예: 12)' }, color: { type: 'string', description: '#RRGGBB' },
      },
      required: ['at'],
    },
  },
  {
    name: 'format_paragraph',
    description: '문단 서식을 바꾼다: 정렬, 줄 간격(%), 들여쓰기, 왼쪽 여백, 문단 위아래 간격(pt), 다음 문단과 함께, 문단 앞 쪽 나눔. 지정하지 않은 속성은 그대로다. 표 셀도 대상이 된다.',
    parameters: {
      type: 'object',
      properties: {
        ...S, at: AT,
        align: { type: 'string', enum: ['left', 'center', 'right', 'justify', 'distribute'] },
        line_spacing: { type: 'number', description: '줄 간격 %(예: 160)' },
        indent_pt: { type: 'number', description: '첫 줄 들여쓰기 pt. 음수면 내어쓰기' },
        left_margin_pt: { type: 'number' }, space_before_pt: { type: 'number' }, space_after_pt: { type: 'number' },
        keep_with_next: { type: 'boolean' }, page_break_before: { type: 'boolean' },
      },
      required: ['at'],
    },
  },
  {
    name: 'apply_style',
    description: '문단에 문서의 스타일(예: 개요 1, 본문)을 입힌다. 쓸 수 있는 스타일 이름은 결과의 styles 에 나온다.',
    parameters: { type: 'object', properties: { ...S, at: AT, style: { type: 'string' } }, required: ['at', 'style'] },
  },
  {
    name: 'insert_table_row',
    description: '표의 row 행 아래(below=true) 또는 위에 빈 행을 넣는다.',
    parameters: { type: 'object', properties: { table: { type: 'string' }, row: { type: 'integer' }, below: { type: 'boolean' } }, required: ['table', 'row'] },
  },
  {
    name: 'delete_table_row',
    description: '표의 row 행을 지운다.',
    parameters: { type: 'object', properties: { table: { type: 'string' }, row: { type: 'integer' } }, required: ['table', 'row'] },
  },
  {
    name: 'insert_table_column',
    description: '표의 col 열 오른쪽(right=true) 또는 왼쪽에 빈 열을 넣는다.',
    parameters: { type: 'object', properties: { table: { type: 'string' }, col: { type: 'integer' }, right: { type: 'boolean' } }, required: ['table', 'col'] },
  },
  {
    name: 'delete_table_column',
    description: '표의 col 열을 지운다.',
    parameters: { type: 'object', properties: { table: { type: 'string' }, col: { type: 'integer' } }, required: ['table', 'col'] },
  },
  {
    name: 'merge_cells',
    description: '표에서 (from_row, from_col)부터 (to_row, to_col)까지 사각 영역의 셀을 하나로 합친다.',
    parameters: { type: 'object', properties: { table: { type: 'string' }, from_row: { type: 'integer' }, from_col: { type: 'integer' }, to_row: { type: 'integer' }, to_col: { type: 'integer' } }, required: ['table', 'from_row', 'from_col', 'to_row', 'to_col'] },
  },
  {
    name: 'split_cell',
    description: '병합된 셀을 원래 칸들로 나눈다.',
    parameters: { type: 'object', properties: { table: { type: 'string' }, row: { type: 'integer' }, col: { type: 'integer' } }, required: ['table', 'row', 'col'] },
  },
  {
    name: 'table_props',
    description: '표가 쪽 경계에 걸릴 때의 처리(page_break: split=나눔, cell=셀 단위로 나눔, none=나누지 않음)와 제목 줄 반복(repeat_header)을 정한다. 한 쪽에 들어가는 작은 표는 none 이 잘림을 막는다.',
    parameters: { type: 'object', properties: { table: { type: 'string' }, page_break: { type: 'string', enum: ['split', 'cell', 'none'] }, repeat_header: { type: 'boolean' } }, required: ['table'] },
  },
  {
    name: 'table_formula',
    description: '표 셀에 계산식 결과를 넣는다. formula 예: =SUM(B2:B5), =AVG(C2:C4), =B2*C2. 셀 주소는 열 A,B,C… 와 행 1,2,3…(1부터) 이다.',
    parameters: { type: 'object', properties: { table: { type: 'string' }, row: { type: 'integer' }, col: { type: 'integer' }, formula: { type: 'string' } }, required: ['table', 'row', 'col', 'formula'] },
  },
  {
    name: 'create_table',
    description: 'after_para 문단 뒤에 새 표를 만들고 rows(행마다 셀 글자 배열)로 채운다. 첫 행을 머리글로 쓰면 된다.',
    parameters: { type: 'object', properties: { ...S, after_para: { type: 'integer' }, rows: { type: 'array', items: { type: 'array', items: { type: 'string' } } } }, required: ['after_para', 'rows'] },
  },
  {
    name: 'delete_table',
    description: '표 하나를 통째로 지운다.',
    parameters: { type: 'object', properties: { table: { type: 'string' } }, required: ['table'] },
  },
  {
    name: 'set_list',
    description: '문단에 자동 문단 번호(number: 수준 0=1. 1=가. 2=1) 3=가) …)를 달거나 없앤다(none). bullet 은 ○ 같은 기호를 글자로 앞에 붙인다(이미 기호가 있으면 건너뜀). 자동 번호는 글 앞에 손으로 쓴 번호가 있으면 겹치니 먼저 replace_paragraph 에 keep_bullet=false 로 뺀다.',
    parameters: {
      type: 'object',
      properties: {
        ...S, at: { type: 'string', description: 'p5 또는 p5-p9' }, kind: { type: 'string', enum: ['number', 'bullet', 'none'] },
        level: { type: 'integer', description: '0부터. 번호 수준(0=1. 1=가. 2=1) …)' }, bullet: { type: 'string', description: '글머리표 문자(기본 ○)' },
      },
      required: ['at', 'kind'],
    },
  },
  {
    name: 'set_header_footer',
    description: '머리말(header)이나 꼬리말(footer)의 글을 넣거나 바꾼다. 모든 쪽에 들어간다. 쪽 번호는 넣을 수 없다(rhwp 0.8.6 에서 쪽 번호 필드가 저장 때 사라지거나 문서를 깨뜨린다. 한컴 한글에서 넣으라고 안내하라).',
    parameters: { type: 'object', properties: { which: { type: 'string', enum: ['header', 'footer'] }, text: { type: 'string' }, align: { type: 'string', enum: ['left', 'center', 'right'] } }, required: ['which', 'text'] },
  },
  {
    name: 'add_footnote',
    description: '문단 para 의 after 글자 바로 뒤(생략하면 문단 끝)에 각주 번호를 달고 쪽 아래에 각주 글을 넣는다. 출처나 근거를 밝힐 때 쓴다.',
    parameters: { type: 'object', properties: { ...S, para: { type: 'integer' }, after: { type: 'string' }, text: { type: 'string' } }, required: ['para', 'text'] },
  },
  {
    name: 'set_field',
    description: '누름틀 필드에 값을 넣는다. read_document 끝의 필드 목록에 있는 이름만 쓸 수 있다.',
    parameters: { type: 'object', properties: { name: { type: 'string' }, value: { type: 'string' } }, required: ['name', 'value'] },
  },
];

// ── 실행 ─────────────────────────────────────────────
// 반환: { result: 모델에 돌려줄 객체, mark: 화면 교정 기록(편집일 때만) }

const READ_ONLY = new Set(['read_document', 'search_text']);

const allTables = (doc) => J(doc.getControls()).filter((c) => c.ctrlId === 'tbl').length;

/**
 * 도구 하나를 원자적으로 실행한다. 편집 도구는 실행 전 스냅샷을 떠 두고, 실패하거나 의도하지 않게
 * 표가 사라지면(셀 안의 표가 든 셀을 통째로 바꾼 경우 등) 스냅샷으로 되돌린다. 그래야 실패한 호출이
 * 사본 문서에 흔적을 남겨 편집기에 재생할 편집 목록과 어긋나지 않는다.
 */
export function runTool(doc, name, a = {}) {
  if (READ_ONLY.has(name)) {
    try {
      return exec(doc, name, a);
    } catch (e) {
      return { result: { ok: false, error: String(e?.message ?? e) } };
    }
  }
  const snap = doc.saveSnapshot();
  try {
    const pagesBefore = doc.pageCount();
    const tablesBefore = allTables(doc);
    const out = exec(doc, name, a);
    const lost = name === 'delete_table' ? 0 : tablesBefore - allTables(doc); // 표 삭제는 안에 든 표까지 지우는 게 정상
    if (lost > 0) throw new Error('이 편집은 셀 안에 든 표를 지웁니다. 되돌렸습니다. 그 셀은 통째로 바꾸지 말고 find_replace 로 글만 고치세요.');
    if (!out.result.ok) doc.restoreSnapshot(snap);
    // 쪽수 드리프트: 편집으로 쪽수가 바뀌면 알린다(양식이 한 쪽을 넘기는 사고를 막는다).
    else if (doc.pageCount() !== pagesBefore) out.result.pages = `쪽수가 ${pagesBefore}쪽에서 ${doc.pageCount()}쪽으로 바뀌었습니다.`;
    return out;
  } catch (e) {
    doc.restoreSnapshot(snap);
    return { result: { ok: false, error: String(e?.message ?? e) } };
  } finally {
    doc.discardSnapshot(snap);
  }
}

function exec(doc, name, a) {
  const s = a.section ?? 0;
  switch (name) {
    case 'read_document':
      return { result: { ok: true, document: outline(doc, { from: a.from_para, to: a.to_para }) } };

    case 'search_text': {
      if (!a.query) throw new Error('query 가 비었습니다.');
      const tables = listTables(doc);
      const hits = J(doc.searchAllText(a.query, !!a.case_sensitive, true)).slice(0, 50).map((h) => {
        if (h.cellContext) {
          const cx = h.cellContext;
          const t = tables.find((x) => x.section === h.sec && x.para === cx.parentPara && x.ctrl === cx.ctrlIdx);
          const info = J(doc.getCellInfo(h.sec, cx.parentPara, cx.ctrlIdx, cx.cellIdx));
          const text = cellParaText(doc, t, cx.cellIdx, cx.cellPara);
          return { at: `${t?.id ?? '?'}r${info.row}c${info.col}`, context: text.slice(Math.max(0, h.charOffset - 20), h.charOffset + h.length + 20) };
        }
        const text = paraText(doc, h.sec, h.para);
        return { at: `p${h.para}`, context: text.slice(Math.max(0, h.charOffset - 20), h.charOffset + h.length + 20) };
      });
      return { result: { ok: true, count: hits.length, hits } };
    }

    case 'replace_paragraph': {
      checkPara(doc, s, a.para);
      const before = paraText(doc, s, a.para);
      const [first0, ...rest] = clean(a.text).split('\n');
      const first = a.keep_bullet === false ? first0 : keepBullet(before, first0);
      const plain = a.keep_style ? null : plainStyleForPara(doc, s, a.para);
      const len = doc.getParagraphLength(s, a.para);
      if (len) doc.replaceText(s, a.para, 0, len, first);
      else if (first) doc.insertText(s, a.para, 0, first);
      if (rest.length) insertParas(doc, s, a.para, rest);
      if (plain) {
        for (let p = a.para; p <= a.para + rest.length; p++) {
          const l = doc.getParagraphLength(s, p);
          if (l) doc.applyCharFormat(s, p, 0, l, JSON.stringify(plain.props));
        }
      }
      return {
        result: {
          ok: true,
          ...(first !== first0 && { note: '원문의 글머리 기호를 지켰습니다.' }),
          ...(plain && { style: plainNote(plain) }),
          ...(rest.length && { shift: shifted(rest.length, a.para) }),
        },
        mark: { kind: 'replace', where: `p${a.para}`, before, after: [first, ...rest].join('\n') },
      };
    }

    case 'insert_paragraphs': {
      checkPara(doc, s, a.after_para);
      const texts = a.texts.map(clean);
      insertParas(doc, s, a.after_para, texts);
      return {
        result: { ok: true, inserted: texts.map((_, i) => `p${a.after_para + 1 + i}`), note: shifted(texts.length, a.after_para) },
        mark: { kind: 'insert', where: `p${a.after_para} 뒤`, after: texts.join('\n') },
      };
    }

    case 'delete_paragraphs': {
      const { from_para: f, to_para: t } = a;
      checkPara(doc, s, f);
      checkPara(doc, s, t);
      if (f > t) throw new Error('from_para 가 to_para 보다 큽니다.');
      if (f === 0) throw new Error('p0 은 구역 정의를 담고 있어 지울 수 없습니다. 글만 비우려면 replace_paragraph 로 빈 글을 넣으세요.');
      const withTable = listTables(doc).find((x) => x.section === s && x.para >= f && x.para <= t);
      if (withTable) throw new Error(`p${withTable.para} 에 ${withTable.id} 가 있습니다. 표는 delete_table 로 지우세요.`);
      const before = [];
      for (let p = f; p <= t; p++) before.push(paraText(doc, s, p));
      for (let p = t; p >= f; p--) doc.deleteParagraph(s, p);
      return {
        result: { ok: true, note: shifted(-(t - f + 1), f) },
        mark: { kind: 'delete', where: `p${f}${t > f ? `~p${t}` : ''}`, before: before.join('\n') },
      };
    }

    case 'find_replace': {
      if (!a.find) throw new Error('find 가 비었습니다.');
      let replace = clean(a.replace);
      if (a.keep_width) {
        if (replace.length > a.find.length) throw new Error(`keep_width: 바꿀 글(${replace.length}자)이 원래 폭(${a.find.length}자)보다 깁니다. 더 짧게 쓰세요.`);
        replace = replace.padEnd(a.find.length, ' ');
      }
      const found = J(doc.searchAllText(a.find, true, true));
      if (!found.length) return { result: { ok: false, error: `「${a.find}」를 찾지 못했습니다. 자리표시가 공백이나 탭으로 쪼개져 있을 수 있으니 search_text 로 더 짧게 찾아보세요.` } };
      if (a.expected_count != null && found.length !== a.expected_count) {
        const where = exec(doc, 'search_text', { query: a.find, case_sensitive: true }).result.hits.map((h) => h.at);
        return { result: { ok: false, error: `「${a.find}」가 ${found.length}곳에 있어 기대한 ${a.expected_count}곳과 다릅니다. 바꾸지 않았습니다. 위치: ${where.join(', ')}. 한 곳만 바꾸려면 replace_paragraph 나 set_cell 을 쓰세요.` } };
      }
      const r = J(doc.replaceAll(a.find, replace, true));
      return { result: { ok: true, count: r.count }, mark: { kind: 'replace', where: `전체 ${r.count}곳`, before: a.find, after: replace } };
    }

    case 'set_cell': {
      const t = findTable(doc, a.table);
      const c = findCell(doc, t, a.row, a.col);
      const before = cellText(doc, t, c);
      const text = clean(a.text);
      const plain = a.keep_style ? null : plainStyleForCell(doc, t, c);
      setCellText(doc, t, c, text);
      if (plain) applyPlainToCell(doc, t, c, plain);
      return { result: { ok: true, ...(plain && { style: plainNote(plain) }) }, mark: { kind: 'replace', where: `${t.id} r${a.row}c${a.col}`, before, after: text } };
    }

    case 'fill_by_label': {
      const want = norm(a.label);
      const hits = [];
      for (const t of listTables(doc)) {
        for (const c of tableCells(doc, t).cells) if (norm(cellText(doc, t, c.idx)) === want) hits.push({ t, c });
      }
      if (!hits.length) throw new Error(`라벨 「${a.label}」 칸을 찾지 못했습니다. 표의 라벨 글자를 그대로 쓰세요.`);
      if (hits.length > 1 && !a.occurrence) {
        throw new Error(`라벨 「${a.label}」가 ${hits.length}곳입니다: ${hits.map((h, i) => `${i + 1}) ${h.t.id}r${h.c.row}c${h.c.col}`).join(', ')}. occurrence 로 고르세요.`);
      }
      const h = hits[(a.occurrence ?? 1) - 1];
      if (!h) throw new Error(`occurrence 는 1~${hits.length} 입니다.`);
      const below = a.direction === 'below';
      const row = below ? h.c.row + h.c.rowSpan : h.c.row;
      const col = below ? h.c.col : h.c.col + h.c.colSpan;
      const c = findCell(doc, h.t, row, col);
      const before = cellText(doc, h.t, c);
      const text = clean(a.text);
      const plain = a.keep_style ? null : plainStyleForCell(doc, h.t, c);
      setCellText(doc, h.t, c, text);
      if (plain) applyPlainToCell(doc, h.t, c, plain);
      return {
        result: { ok: true, cell: `${h.t.id}r${row}c${col}`, ...(plain && { style: plainNote(plain) }) },
        mark: { kind: 'replace', where: `${h.t.id} r${row}c${col}`, before, after: text },
      };
    }

    case 'format_text': {
      const props = JSON.stringify(charProps(a));
      let n = 0;
      for (const x of expandTargets(doc, a.at, s)) {
        for (const r of rangesIn(doc, x, a.text)) {
          if (x.kind === 'para') doc.applyCharFormat(x.s, x.p, r.start, r.end, props);
          else doc.applyCharFormatInCell(x.t.section, x.t.para, x.t.ctrl, x.c, r.i, r.start, r.end, props);
          n++;
        }
      }
      if (!n) throw new Error(a.text ? `「${a.text}」를 ${a.at} 에서 찾지 못했습니다.` : `${a.at} 에 글자가 없습니다.`);
      const what = ['bold', 'italic', 'underline', 'strikethrough', 'size_pt', 'color'].filter((k) => a[k] != null).map((k) => `${k}=${a[k]}`).join(', ');
      return { result: { ok: true, ranges: n }, mark: { kind: 'format', where: String(a.at), after: `${a.text ? `「${a.text}」 ` : ''}${what}` } };
    }

    case 'format_paragraph': {
      const props = JSON.stringify(paraProps(a));
      const targets = expandTargets(doc, a.at, s);
      for (const x of targets) {
        if (x.kind === 'para') doc.applyParaFormat(x.s, x.p, props);
        else {
          const n = doc.getCellParagraphCount(x.t.section, x.t.para, x.t.ctrl, x.c);
          for (let i = 0; i < n; i++) doc.applyParaFormatInCell(x.t.section, x.t.para, x.t.ctrl, x.c, i, props);
        }
      }
      const what = Object.entries(a).filter(([k]) => !['at', 'section'].includes(k)).map(([k, v]) => `${k}=${v}`).join(', ');
      return { result: { ok: true, targets: targets.length }, mark: { kind: 'format', where: String(a.at), after: `문단 ${what}` } };
    }

    case 'apply_style': {
      const styles = J(doc.getStyleList());
      const st = styles.find((x) => norm(x.name) === norm(a.style) || x.englishName === a.style);
      if (!st) return { result: { ok: false, error: `스타일 「${a.style}」가 없습니다.`, styles: styles.map((x) => x.name) } };
      const targets = expandTargets(doc, a.at, s);
      const doubled = [];
      for (const x of targets) {
        if (x.kind === 'para') {
          doc.applyStyle(x.s, x.p, st.id);
          // 개요 스타일은 번호를 자동으로 붙인다. 글에 손으로 쓴 번호가 있으면 「1. 2. 제목」처럼 겹친다(한컴 실측).
          if (/^개요|^Outline/.test(st.name) && BULLET.test(paraText(doc, x.s, x.p))) doubled.push(`p${x.p}`);
        } else {
          const n = doc.getCellParagraphCount(x.t.section, x.t.para, x.t.ctrl, x.c);
          for (let i = 0; i < n; i++) doc.applyCellStyle(x.t.section, x.t.para, x.t.ctrl, x.c, i, st.id);
        }
      }
      return {
        result: {
          ok: true, targets: targets.length,
          ...(doubled.length && { warning: `${doubled.join(', ')} 는 글 앞에 번호가 있어 개요 자동 번호와 겹칩니다. replace_paragraph 에 keep_bullet=false 로 번호를 뺀 글을 넣으세요.` }),
        },
        mark: { kind: 'format', where: String(a.at), after: `스타일 ${st.name}` },
      };
    }

    case 'insert_table_row': {
      const t = findTable(doc, a.table);
      const r = J(doc.insertTableRow(t.section, t.para, t.ctrl, a.row, a.below ?? true));
      return { result: { ok: true, rowCount: r.rowCount }, mark: { kind: 'table', where: t.id, after: `행 추가 (r${a.row} ${a.below ?? true ? '아래' : '위'})` } };
    }

    case 'delete_table_row': {
      const t = findTable(doc, a.table);
      const r = J(doc.deleteTableRow(t.section, t.para, t.ctrl, a.row));
      return { result: { ok: true, rowCount: r.rowCount }, mark: { kind: 'table', where: t.id, after: `r${a.row} 행 삭제` } };
    }

    case 'insert_table_column': {
      const t = findTable(doc, a.table);
      const r = J(doc.insertTableColumn(t.section, t.para, t.ctrl, a.col, a.right ?? true));
      return { result: { ok: true, colCount: r.colCount }, mark: { kind: 'table', where: t.id, after: `열 추가 (c${a.col} ${a.right ?? true ? '오른쪽' : '왼쪽'})` } };
    }

    case 'delete_table_column': {
      const t = findTable(doc, a.table);
      const r = J(doc.deleteTableColumn(t.section, t.para, t.ctrl, a.col));
      return { result: { ok: true, colCount: r.colCount }, mark: { kind: 'table', where: t.id, after: `c${a.col} 열 삭제` } };
    }

    case 'merge_cells': {
      const t = findTable(doc, a.table);
      findCell(doc, t, a.from_row, a.from_col);
      findCell(doc, t, a.to_row, a.to_col);
      const r = J(doc.mergeTableCells(t.section, t.para, t.ctrl, a.from_row, a.from_col, a.to_row, a.to_col));
      return { result: { ok: true, cellCount: r.cellCount }, mark: { kind: 'table', where: t.id, after: `r${a.from_row}c${a.from_col}~r${a.to_row}c${a.to_col} 병합` } };
    }

    case 'split_cell': {
      const t = findTable(doc, a.table);
      findCell(doc, t, a.row, a.col);
      const r = J(doc.splitTableCell(t.section, t.para, t.ctrl, a.row, a.col));
      return { result: { ok: true, cellCount: r.cellCount }, mark: { kind: 'table', where: t.id, after: `r${a.row}c${a.col} 나누기` } };
    }

    case 'table_props': {
      const t = findTable(doc, a.table);
      const props = {};
      if (a.page_break) {
        if (!(a.page_break in PAGE_BREAK)) throw new Error('page_break 는 split, cell, none 중 하나입니다.');
        props.pageBreak = PAGE_BREAK[a.page_break];
      }
      if (typeof a.repeat_header === 'boolean') props.repeatHeader = a.repeat_header;
      if (!Object.keys(props).length) throw new Error('바꿀 표 속성이 없습니다(page_break, repeat_header).');
      doc.setTableProperties(t.section, t.para, t.ctrl, JSON.stringify(props));
      const label = { split: '쪽 경계에서 나눔', cell: '셀 단위로 나눔', none: '나누지 않음' };
      return {
        result: { ok: true },
        mark: { kind: 'table', where: t.id, after: [a.page_break && label[a.page_break], a.repeat_header != null && `제목 줄 반복 ${a.repeat_header ? '켬' : '끔'}`].filter(Boolean).join(', ') },
      };
    }

    case 'table_formula': {
      const t = findTable(doc, a.table);
      const c = findCell(doc, t, a.row, a.col);
      const before = cellText(doc, t, c);
      const r = J(doc.evaluateTableFormula(t.section, t.para, t.ctrl, a.row, a.col, a.formula, true));
      if (!r.ok) throw new Error(`계산식 오류: ${r.error ?? JSON.stringify(r)}`);
      return { result: { ok: true, value: r.result }, mark: { kind: 'replace', where: `${t.id} r${a.row}c${a.col}`, before, after: `${r.result} (${a.formula})` } };
    }

    case 'create_table': {
      checkPara(doc, s, a.after_para);
      const rows = a.rows.map((r) => r.map(clean));
      const cols = Math.max(...rows.map((r) => r.length));
      if (!rows.length || !cols) throw new Error('rows 가 비었습니다.');
      const at = a.after_para + 1;
      doc.insertParagraph(s, at);
      const made = J(doc.createTable(s, at, 0, rows.length, cols));
      const t = { id: '새 표', section: s, para: made.paraIdx, ctrl: made.controlIdx };
      rows.forEach((row, r) => row.forEach((text, c) => text && setCellText(doc, t, findCell(doc, t, r, c), text)));
      const id = listTables(doc).find((x) => x.section === s && x.para === made.paraIdx)?.id;
      return {
        result: { ok: true, table: id, para: `p${made.paraIdx}`, note: `${shifted(1, a.after_para)} 표 번호도 다시 매겨졌을 수 있습니다.` },
        mark: { kind: 'insert', where: `p${a.after_para} 뒤 표 ${rows.length}×${cols}`, after: rows.map((r) => r.join(' | ')).join('\n') },
      };
    }

    case 'delete_table': {
      const t = findTable(doc, a.table);
      doc.deleteTableControl(t.section, t.para, t.ctrl);
      return { result: { ok: true, note: '표 번호가 다시 매겨졌습니다.' }, mark: { kind: 'delete', where: t.id, before: '표 삭제' } };
    }

    case 'set_list': {
      const targets = expandTargets(doc, a.at, s);
      if (targets.some((x) => x.kind !== 'para')) throw new Error('set_list 는 본문 문단(p5, p5-p9)에만 쓴다.');
      // 자동 글머리표(headType Bullet)는 rhwp 에서 저장해도 한컴 한글에 기호가 보이지 않는다(실측).
      // 공문과 계획서는 □ ○ - 를 글자로 쓰는 것이 관행이므로 글머리표는 글자로 앞에 붙인다.
      if (a.kind === 'bullet') {
        const mark = a.bullet || '○';
        for (const x of targets) {
          const text = paraText(doc, x.s, x.p);
          if (!text || BULLET.test(text)) continue;
          doc.insertText(x.s, x.p, 0, `${mark} `);
        }
        return { result: { ok: true, note: '글머리표는 글자로 붙였다(자동 글머리표는 한컴에서 보이지 않음).' }, mark: { kind: 'format', where: String(a.at), after: `글머리표 ${mark}` } };
      }
      let props;
      if (a.kind === 'none') props = { headType: 'None', numberingId: 0 };
      else if (a.kind === 'number') props = { headType: 'Number', numberingId: doc.ensureDefaultNumbering(), paraLevel: Math.max(0, Math.min(6, a.level ?? 0)) };
      else throw new Error('kind 는 number, bullet, none 중 하나입니다.');
      const doubled = [];
      for (const x of targets) {
        doc.applyParaFormat(x.s, x.p, JSON.stringify(props));
        if (a.kind !== 'none' && BULLET.test(paraText(doc, x.s, x.p))) doubled.push(`p${x.p}`);
      }
      const label = a.kind === 'number' ? `자동 번호(수준 ${props.paraLevel})` : '자동 번호 없앰';
      return {
        result: { ok: true, ...(doubled.length && { warning: `${doubled.join(', ')} 는 글 앞에 손으로 쓴 번호나 기호가 있어 겹칩니다. keep_bullet=false 로 빼세요.` }) },
        mark: { kind: 'format', where: String(a.at), after: label },
      };
    }

    case 'set_header_footer': {
      const isHeader = a.which === 'header';
      if (!isHeader && a.which !== 'footer') throw new Error('which 는 header 또는 footer 입니다.');
      if (/쪽\s*번호|페이지\s*번호|\{쪽\}|page/i.test(a.text)) throw new Error('쪽 번호는 넣을 수 없습니다(rhwp 0.8.6 에서 저장 때 사라지거나 문서를 깨뜨림). 글만 넣고, 쪽 번호는 한컴 한글에서 넣도록 사용자에게 안내하세요.');
      const text = clean(a.text);
      let hf = J(doc.getHeaderFooter(s, isHeader, 0));
      const before = hf.exists ? hf.text : '';
      if (!hf.exists) doc.createHeaderFooter(s, isHeader, 0);
      for (let i = J(doc.getHeaderFooter(s, isHeader, 0)).paraCount - 1; i >= 1; i--) doc.mergeParagraphInHeaderFooter(s, isHeader, 0, i);
      const len = J(doc.getHeaderFooterParaInfo(s, isHeader, 0, 0)).charCount;
      if (len) doc.deleteTextInHeaderFooter(s, isHeader, 0, 0, 0, len);
      if (text) doc.insertTextInHeaderFooter(s, isHeader, 0, 0, 0, text);
      if (a.align) doc.applyParaFormatInHf(s, isHeader, 0, 0, JSON.stringify({ alignment: ALIGN[a.align] }));
      hf = J(doc.getHeaderFooter(s, isHeader, 0));
      return { result: { ok: true, text: hf.text }, mark: { kind: 'replace', where: isHeader ? '머리말' : '꼬리말', before, after: text } };
    }

    case 'add_footnote': {
      checkPara(doc, s, a.para);
      const text = paraText(doc, s, a.para);
      let offset = text.length;
      if (a.after) {
        const k = text.indexOf(a.after);
        if (k < 0) throw new Error(`p${a.para} 에서 「${a.after}」를 찾지 못했습니다.`);
        offset = k + a.after.length;
      }
      const r = J(doc.insertFootnote(s, a.para, offset));
      if (!r.ok) throw new Error(`각주를 넣지 못했습니다: ${JSON.stringify(r)}`);
      const info = J(doc.getFootnoteInfo(s, a.para, r.controlIdx));
      doc.insertTextInFootnote(s, a.para, r.controlIdx, 0, info.totalTextLen ?? 0, clean(a.text));
      return { result: { ok: true, number: r.footnoteNumber }, mark: { kind: 'insert', where: `p${a.para} 각주 ${r.footnoteNumber}`, after: clean(a.text) } };
    }

    // ── 동시 편집 내부 도구(TOOLS 에 없음, AI 는 부르지 않는다) ──
    // 손 편집을 글 차이로 옮길 때 쓴다. 바뀐 구간만 지우고 넣어 나머지 글의 서식을 지킨다.
    case 'splice_paragraph': {
      checkPara(doc, s, a.para);
      const before = paraText(doc, s, a.para);
      if (a.offset + a.len > before.length) throw new Error(`p${a.para} 글 길이(${before.length})를 넘는 구간입니다.`);
      if (a.len) doc.deleteText(s, a.para, a.offset, a.len);
      if (a.text) doc.insertText(s, a.para, a.offset, a.text);
      return { result: { ok: true }, mark: { kind: 'replace', where: `p${a.para}`, before, after: paraText(doc, s, a.para) } };
    }

    case 'splice_cell': {
      const t = findTable(doc, a.table);
      const c = findCell(doc, t, a.row, a.col);
      const i = a.cell_para ?? 0;
      if (i >= doc.getCellParagraphCount(t.section, t.para, t.ctrl, c)) throw new Error(`${t.id}r${a.row}c${a.col} 에 셀 문단 ${i} 이 없습니다.`);
      const before = cellParaText(doc, t, c, i);
      if (a.offset + a.len > before.length) throw new Error('셀 글 길이를 넘는 구간입니다.');
      if (a.len) doc.deleteTextInCell(t.section, t.para, t.ctrl, c, i, a.offset, a.len);
      if (a.text) doc.insertTextInCell(t.section, t.para, t.ctrl, c, i, a.offset, a.text);
      return { result: { ok: true }, mark: { kind: 'replace', where: `${t.id} r${a.row}c${a.col}`, before, after: cellParaText(doc, t, c, i) } };
    }

    case 'set_field': {
      const r = J(doc.setFieldValueByName(a.name, clean(a.value)));
      return { result: { ok: true }, mark: { kind: 'replace', where: `필드 ${a.name}`, before: r.oldValue ?? '', after: a.value } };
    }

    default:
      return { result: { ok: false, error: `모르는 도구: ${name}` } };
  }
}
