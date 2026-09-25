/**
 * 편집 기록 줄 만들기 — CLI(`changes`, `log`)와 에디터의 「로그」 패널(server `/api/logview`)이 같은 글을 보이게 한 곳에 둔다.
 */
const kb = (n) => (n == null ? '' : n < 1024 ? `${n}B` : `${(n / 1024).toFixed(1)}KB`);
const LAYOUT = { hancom: '한글 줄 배치 적용', 'hancom-cache': '한글 줄 배치(캐시)', rhwp: 'rhwp 표 높이 보정(한글 없음)', strip: '더미 줄 배치만 걷음 — 표가 겹칠 수 있다', stored: '저장된 줄 배치 그대로', raw: 'hwp 그대로' };
export function formatLog(e) {
  const t = new Date(e.ts).toLocaleString('sv-SE').slice(5, 16);
  const who = e.by === 'user' ? '사용자' : e.by === 'claude' ? 'Claude' : '';
  switch (e.ev) {
    case 'start': return `${t}  시작      ${e.file}`;
    case 'load': return `${t}  불러옴    ${e.doc} — ${LAYOUT[e.layout] ?? e.layout}${e.tables ? ` ${e.tables}개` : ''}${e.note ? ` (${e.note})` : ''}${e.error ? ` (${e.error})` : ''}`;
    case 'open': return `${t}  열림      ${e.doc} ${kb(e.bytes)}`;
    case 'edit': return `${t}  ${who} 편집 ${e.formatOnly ? '서식이나 개체만' : `${e.count}곳 ${e.refs.join(' ')}${e.count > e.refs.length ? ' …' : ''}`}${e.at ? ` (커서 ${e.at})` : ''}`;
    case 'save': return `${t}  ${who} 저장 ${e.path ?? e.name} ${kb(e.bytes)}${e.via ? ` (${e.via})` : ''}`;
    case 'open-file': return `${t}  ${who} 다른 파일 열기 ${e.names.join(', ')} (${e.via})`;
    case 'error': return `${t}  오류      ${e.cmd ?? ''} ${e.error}`;
    case 'stop': return `${t}  종료`;
    default: return `${t}  ${e.ev} ${JSON.stringify(e)}`;
  }
}

export const localTime = (t) => new Date(t).toTimeString().slice(0, 8);

// 서식 속성 이름과 값(글자 크기는 1/100 pt)
const PROP = {
  fontSize: ['글자 크기', (v) => `${v / 100}pt`], lineSpacing: ['줄 간격', (v) => `${v}%`], lineSpacingType: ['줄 간격 종류'],
  bold: ['진하게'], italic: ['기울임'], underline: ['밑줄'], strikethrough: ['취소선'], textColor: ['글자 색'],
  shadeColor: ['음영 색'], fontId: ['글꼴'], fontIds: ['글꼴'], ratios: ['장평', (v) => `${v?.[0]}%`],
  spacings: ['자간', (v) => `${v?.[0]}%`], relativeSizes: ['상대 크기'], superscript: ['위 첨자'], subscript: ['아래 첨자'],
  alignment: ['정렬'], indent: ['들여쓰기'], marginLeft: ['왼쪽 여백'], marginRight: ['오른쪽 여백'],
  spacingBefore: ['문단 위'], spacingAfter: ['문단 아래'], keepWithNext: ['다음 문단과 함께'], keepLines: ['문단 보호'],
  widowOrphan: ['외톨이줄 보호'], pageBreakBefore: ['앞에서 쪽 나눔'], headType: ['문단 머리'], paraLevel: ['수준', (v) => `${v + 1}`],
};
const propText = (k, [a, b]) => {
  const [name, fmt] = PROP[k] ?? [k];
  const f = (v) => (v === undefined ? '?' : fmt ? fmt(v) : typeof v === 'string' ? v : JSON.stringify(v));
  return `${name} ${f(a)} → ${f(b)}`;
};

/** 이어 친 글자(같은 자리, 붙은 위치)를 한 줄로 묶는다. */
export function coalesceOps(ops) {
  const outOps = [];
  for (const o of ops) {
    const last = outOps[outOps.length - 1];
    if (last && o.type === 'insertText' && last.type === 'insertText' && last.act === o.act && last.atKey === o.atKey &&
        last.end === o.off && o.t - last.t < 5000) {
      outOps[outOps.length - 1] = { ...last, text: last.text + o.text, end: o.end, t: o.t };
    } else outOps.push({ ...o });
  }
  return outOps;
}

/** 실시간 편집 기록 한 줄: [시각] 동작 자리 내용. 서식은 속성: 전 → 후 */
export function formatOp(o) {
  const act = { undo: '되돌리기 ', redo: '다시 실행 ', reserve: '' }[o.act] ?? '';
  let what = '';
  if (o.type === 'insertText') what = `「${o.text}」`;
  else if (o.type === 'deleteText') what = o.text ? `「${o.text}」` : `${o.count}자`;
  if (o.props && Object.keys(o.props).length) what = Object.entries(o.props).map(([k, v]) => propText(k, v)).join(', ');
  return `[${localTime(o.t)}] ${act}${o.label}${o.at ? `  ${o.at}` : ''}${what ? `  ${what}` : ''}`;
}
