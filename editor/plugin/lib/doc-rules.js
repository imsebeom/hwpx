// 행정문서 지식: 문서 종류 감지, 종류별 작성 규칙, 필수 항목(정보 게이트), 검수 규칙, 채울 칸 찾기.
// 규칙의 근거는 사용자 /hwpx 스킬의 references/gonmunseo-2025-writing-rules.md(2025 개정 공문서 작성법,
// 행정업무운영 편람 기반)와 gaejosik-munche.md(교육청 공문 첨부 16건 실측), 그리고 hwpx-kit 검수 규칙이다.
// 브라우저, Node, 스튜디오 플러그인 공용.
import { listTables } from './doc-tools.js';

const J = (s) => (typeof s === 'string' ? JSON.parse(s) : s);

/** 문서의 모든 글 조각을 위치와 함께 훑는다. 본문 문단은 p12, 셀은 T1r2c1. */
export function* textUnits(doc) {
  const secCount = doc.getSectionCount();
  const tables = listTables(doc);
  for (let s = 0; s < secCount; s++) {
    const n = doc.getParagraphCount(s);
    for (let p = 0; p < n; p++) {
      const len = doc.getParagraphLength(s, p);
      const at = secCount > 1 ? `s${s}p${p}` : `p${p}`;
      if (len) yield { at, text: doc.getTextRange(s, p, 0, len) };
      for (const t of tables.filter((x) => x.section === s && x.para === p)) {
        const dim = J(doc.getTableDimensions(t.section, t.para, t.ctrl));
        for (let c = 0; c < dim.cellCount; c++) {
          const info = J(doc.getCellInfo(t.section, t.para, t.ctrl, c));
          const k = doc.getCellParagraphCount(t.section, t.para, t.ctrl, c);
          const parts = [];
          for (let i = 0; i < k; i++) {
            const l = doc.getCellParagraphLength(t.section, t.para, t.ctrl, c, i);
            parts.push(l ? doc.getTextInCell(t.section, t.para, t.ctrl, c, i, 0, l) : '');
          }
          yield { at: `${t.id}r${info.row}c${info.col}`, text: parts.join('\n'), cell: { ...info, table: t.id } };
        }
      }
    }
  }
}

// ── 문서 종류 ────────────────────────────────────────

/** 앞부분 글로 문서 종류를 짐작한다: 공문, 가정통신문, 계획서, 보고서, 일반. */
export function detectDocType(doc) {
  const head = [];
  for (const u of textUnits(doc)) {
    head.push(u.text);
    if (head.length > 40) break;
  }
  const all = head.join('\n');
  const title = head.find((t) => t.trim().length > 4) ?? '';
  if (/^\s*수신\s|(^|\n)\s*(수신|발신|시행)\s|붙임\s+.*끝\./m.test(all)) return '공문';
  if (/가정통신문|학부모님|보호자님/.test(all)) return '가정통신문';
  if (/계획/.test(title)) return '계획서';
  if (/보고|결과/.test(title)) return '보고서';
  return '일반';
}

const COMMON = `[표기 규칙(2025 개정 공문서 작성법)]
- 날짜: 2026. 7. 10. (온점 뒤 한 칸, 월과 일 앞에 0 없음, 일 뒤에도 온점). 요일은 2026. 7. 10.(금). 기간은 2026. 7. 6.~7. 10. 이고 물결표 뒤에 「까지」를 붙이지 않는다.
- 시간: 24시각제 09:00, 13:20 (오전, 오후 쓰지 않음). 범위는 09:30~12:20.
- 금액: 금113,560원(금일십일만삼천오백육십원), 345,000원 (345천원 쓰지 않음, 원 앞 띄움 없음).
- 외국 문자와 약어는 한글을 앞에 두고 괄호에: 업무 협약(MOU), 연구 개발(R&D), 질의응답(Q&A 대신).
- 법률, 규정, 계획서 이름은 홑낫표 「」. 「등」은 생략의 뜻으로만 쓴다(청주, 충주 등 3개 지역).`;

const RULES = {
  공문: `${COMMON}
[공문 규칙]
- 항목 기호는 1. → 가. → 1) → 가) → (1) → (가) → ① → ㉮ 순서. 하위 항목은 두 칸씩 들여 쓰고, 기호와 내용 사이 한 칸. 항목이 하나뿐이면 기호를 붙이지 않는다.
- 본문 시행 문장은 경어 서술형(「~하시기 바랍니다」)이 규범이다. 항목 문장은 평서형 「-다」가 원칙이고 내부 결재는 명사형(-함) 가능.
- 붙임: 본문 다음 줄에 「붙임」 + 두 칸 + 첨부물 이름과 수량. 쌍점을 붙이지 않고, 하나면 번호 1을 쓰지 않는다. 둘 이상이면 1. 2. 로 줄을 나눈다.
- 끝 표시: 본문(또는 붙임) 마지막 글자 뒤 두 칸 띄우고 「끝.」. 표로 끝나면 표 아래 줄에 「끝.」.
- 관련 근거: 「1. 관련: 부서-번호(2026. 2. 1.)「문서 이름」」 형식, 날짜가 앞선 것부터.`,
  계획서: `${COMMON}
[계획서, 보고서 개조식(교육청 공문 첨부 16건 실측)]
- 층: □ 소제목(2~4어절 명사구, 중앙값 5자) > ○ 항목(30자 안팎) > - 세부(40자 안팎) > ※ 참고.
- 종결은 명사구가 4분의 3, 나머지는 「~함, ~됨, ~임」. 「~합니다, ~이다」 같은 서술형과 경어는 쓰지 않는다.
- 항목은 제목처럼 짧게, 근거와 수치는 아래 세부로 내린다. 한 줄에 생각 하나.
- 두괄식: 결론이나 목적을 먼저 쓴다. 「~적, ~의, ~것, ~들」을 줄여 문장을 짧게 한다.`,
  가정통신문: `${COMMON}
[가정통신문]
- 학부모께 드리는 글이므로 서술형 경어(「~합니다, ~바랍니다」)로 쓴다. 개조식 명사형 종결을 쓰지 않는다.
- 행사명, 일시, 장소, 대상, 준비물, 회신 방법과 기한을 빠짐없이 적는다.`,
  일반: COMMON,
};
RULES.보고서 = RULES.계획서;

/** 문서 종류별로 지시문에 덧붙일 규칙 */
export const rulesFor = (type) => RULES[type] ?? RULES.일반;

// 정보 게이트: 새로 쓰기 전에 문서와 대화에 없으면 먼저 물어야 할 항목
const REQUIRED = {
  계획서: ['제목(행사, 사업 이름)', '기간 또는 일시', '대상', '장소', '담당 부서'],
  보고서: ['보고 대상 사업과 기간', '실적 수치', '담당 부서'],
  공문: ['수신', '제목', '붙임 유무와 이름'],
  가정통신문: ['행사명', '일시', '장소', '대상', '준비물', '회신 여부와 기한'],
};
export const requiredFor = (type) => REQUIRED[type] ?? [];

// ── 검수 ────────────────────────────────────────────

const z = (n) => String(Number(n));
const CHECKS = [
  { code: '날짜 표기', re: /\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b/g, fix: (m) => `${m[1]}. ${z(m[2])}. ${z(m[3])}.`, msg: '날짜는 「2026. 7. 10.」 꼴로 쓴다' },
  { code: '날짜 띄어쓰기', re: /\b(20\d{2})\.(\d{1,2})\.(\d{1,2})\.?(?!\d)/g, fix: (m) => `${m[1]}. ${z(m[2])}. ${z(m[3])}.`, msg: '온점 뒤를 한 칸 띄운다' },
  { code: '날짜 0 채움', re: /\b(20\d{2})\. (0\d)\. (\d{1,2})\./g, fix: (m) => `${m[1]}. ${z(m[2])}. ${z(m[3])}.`, msg: '월과 일 앞에 0을 쓰지 않는다' },
  { code: '날짜 0 채움', re: /\b(20\d{2})\. (\d{1,2})\. (0\d)\./g, fix: (m) => `${m[1]}. ${z(m[2])}. ${z(m[3])}.`, msg: '월과 일 앞에 0을 쓰지 않는다' },
  { code: '날짜 끝 온점', re: /\b(20\d{2})\. (\d{1,2})\. (\d{1,2})(?![.\d])/g, fix: (m) => `${m[1]}. ${m[2]}. ${m[3]}.`, msg: '일 뒤에도 온점을 찍는다(요일은 「10.(금)」)' },
  { code: '기간 까지', re: /[~∼～][^\n~∼～]{0,20}?까지/g, msg: '물결표로 기간을 쓸 때는 「까지」를 붙이지 않는다' },
  { code: '시간 표기', re: /(오전|오후|낮|밤|새벽)\s?(\d{1,2})시(?:\s?(\d{1,2})분)?/g, msg: '24시각제(09:00, 15:30)로 쓴다' },
  { code: '시간 표기', re: /(?<![\d:])(\d{1,2})시\s?(\d{1,2})분/g, fix: (m) => `${m[1].padStart(2, '0')}:${m[2].padStart(2, '0')}`, msg: '시와 분은 쌍점으로(14:30)' },
  { code: '시간 표기', re: /(?<![\d:])(\d):(\d{2})(?!\d)/g, fix: (m) => `0${m[1]}:${m[2]}`, msg: '10 미만 시각은 0을 넣는다(09:00)' },
  { code: '시간 표기', re: /(\d{1,2}) : (\d{2})/g, fix: (m) => `${m[1]}:${m[2]}`, msg: '쌍점 양쪽을 띄우지 않는다' },
  { code: '금액 표기', re: /금\s+(\d[\d,]*)\s*원/g, fix: (m) => `금${m[1]}원`, msg: '「금」과 숫자 사이, 숫자와 「원」 사이를 띄우지 않는다' },
  { code: '금액 표기', re: /(\d[\d,]*)\s+원(?![가-힣])/g, fix: (m) => `${m[1]}원`, msg: '숫자와 「원」 사이를 띄우지 않는다' },
  { code: '금액 표기', re: /\d+천\s?원/g, msg: '「345천원」 대신 「345,000원」' },
  { code: '외국 문자', re: /(?<![(\w가-힣])(Q&A|MOU|R&D|OECD|1F|3D)(?![\w)])/g, msg: '한글을 앞에 쓰고 약어는 괄호에(업무 협약(MOU))' },
  { code: '남은 자리표시', re: /\{\{[^}]*\}\}|[○◯]{2,}|□{3,}|\(여기에[^)]*\)|\(예[:시][^)]*\)|←\s*해당\s*시|\((?:[^()]*)적으세요\)|OOO/g, msg: '채우지 않은 자리표시가 남아 있다' },
  { code: '개인정보', re: /\b\d{6}-[1-4]\d{6}\b/g, msg: '주민등록번호로 보인다' },
  { code: '개인정보', re: /\b01[016789]-?\d{3,4}-?\d{4}\b/g, msg: '휴대전화 번호로 보인다' },
  { code: '개인정보', re: /[\w.+-]+@[\w-]+\.[\w.]+/g, msg: '전자 우편 주소로 보인다' },
  { code: '붙임 표기', re: /붙임\s*:/g, msg: '「붙임」 다음에 쌍점을 붙이지 않는다', only: '공문' },
  { code: '붙임 표기', re: /붙임 (?! )\S/g, msg: '「붙임」 다음은 두 칸 띄운다', only: '공문' },
  { code: '끝 표기', re: /\S ?끝\.$/gm, msg: '「끝.」 앞은 두 칸 띄운다', only: '공문' },
];

/**
 * 문서를 검수해 위반 목록을 돌려준다. type 이 '공문'이면 공문 전용 규칙과 「끝.」 유무도 본다.
 * 반환: [{code, msg, at, context, found, fix?}]
 */
export function inspect(doc, type = detectDocType(doc)) {
  const out = [];
  let hasEnd = false;
  for (const u of textUnits(doc)) {
    if (/  끝\.\s*$/m.test(u.text)) hasEnd = true;
    for (const ck of CHECKS) {
      if (ck.only && ck.only !== type) continue;
      for (const m of u.text.matchAll(ck.re)) {
        out.push({
          code: ck.code, msg: ck.msg, at: u.at, found: m[0],
          context: u.text.slice(Math.max(0, m.index - 15), m.index + m[0].length + 15),
          ...(ck.fix && { fix: ck.fix(m) }),
        });
      }
    }
  }
  if (type === '공문' && !hasEnd) out.push({ code: '끝 표기', msg: '본문(또는 붙임) 끝에 「  끝.」이 없다', at: '', found: '', context: '' });
  return out;
}

// ── 채울 칸 ──────────────────────────────────────────

const SLOT = /\{\{[^}]*\}\}|[○◯]{2,}|\(여기에[^)]*\)|\(예[:시][^)]*\)|\((?:[^()]*)적으세요\)|_{3,}/;

/**
 * 채워야 할 자리를 찾는다: 자리표시 문구가 든 문단과 셀, 그리고 라벨 칸 오른쪽의 빈 셀.
 * 반환: [{at, label, text}]
 */
export function findSlots(doc) {
  const units = [...textUnits(doc)];
  const slots = [];
  for (const u of units) {
    if (SLOT.test(u.text)) slots.push({ at: u.at, label: u.cell ? labelLeft(units, u) : '', text: u.text.slice(0, 60) });
  }
  // 라벨 오른쪽 빈 셀: 같은 행 왼쪽 셀이 짧은 글(라벨)이고 이 셀이 비었으면 채울 칸이다.
  for (const u of units) {
    if (!u.cell || u.text.trim()) continue;
    const label = labelLeft(units, u);
    if (label && label.length <= 15) slots.push({ at: u.at, label, text: '' });
  }
  return slots;
}

function labelLeft(units, u) {
  const left = units.find((x) => x.cell && x.cell.table === u.cell.table && x.cell.row === u.cell.row && x.cell.col + x.cell.colSpan === u.cell.col);
  return left?.text.trim() ?? '';
}
