"""공문서 표기법 검수 — 「행정업무의 운영 및 혁신에 관한 규정」 시행규칙과 행정안전부 행정업무운영 편람의
날짜, 시간, 금액, 붙임, 쌍점, 물결표 표기와 두음법칙, 외래어, 차별 표현을 정규식으로 검사한다.

출처: kordoc(https://github.com/chrisryugj/kordoc, MIT) src/hwpx/gongmun-lint.ts v4.15.7 의 규칙을 파이썬
표준 라이브러리로 옮겼다(그 원전은 jkf87/hwpx-skill gonmun_lint.py). 파이썬 `re` 는 길이가 바뀌는 뒤 보기를
지원하지 않아, 그런 조건은 일치한 뒤 앞 글을 따로 검사한다. kordoc 의 AI 문체 규칙 두 개(줄표, 굵게 남용)는
옮기지 않았다 — 줄표 대신 가운뎃점을 권해 사용자 문체 규칙과 부딪치고, AI 문체는 references/style_gate 가 본다.

검사는 조언용이다. 생성을 막지 않고 위반을 알려 준다. 명령줄은 error 가 있으면 종료 코드 1.

    python gongmun_lint.py 문서.hwpx [--document]      # hwpx: 본문과 표 칸 글을 뽑아 검사(표 칸은 서식 라벨 규칙 제외)
    python gongmun_lint.py 원고.md | 원고.txt | -        # 마크다운, 글, 표준 입력
    --document : 붙임이 있으면 「끝.」 표시를 확인한다(완성 원고 검사용)
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

# 외래어 오기 → 표준 표기(국립국어원 외래어 표기법 용례)
LOANWORD_FIXES = [
    ("컨텐츠", "콘텐츠"),
    ("어플리케이션", "애플리케이션"),
    ("메세지", "메시지"),
    ("리더쉽", "리더십"),
    ("워크샵", "워크숍"),
    ("스케쥴", "스케줄"),
    ("악세사리", "액세서리"),
    ("네비게이션", "내비게이션"),
    ("타겟", "타깃"),
    ("화이팅", "파이팅"),
    ("비지니스", "비즈니스"),
    ("프리젠테이션", "프레젠테이션"),
    ("라이센스", "라이선스"),
    ("캐비넷", "캐비닛"),
    ("렌트카", "렌터카"),
    ("플랭카드", "플래카드"),
    ("플랜카드", "플래카드"),
    ("컨셉", "콘셉트"),
    ("심볼", "심벌"),
    ("카달로그", "카탈로그"),
    ("팜플렛", "팸플릿"),
    ("팜플릿", "팸플릿"),
    ("리모콘", "리모컨"),
    ("에어콘", "에어컨"),
    ("알콜", "알코올"),
    ("발란스", "밸런스"),
    ("매니아", "마니아"),
    ("코메디", "코미디"),
    ("판넬", "패널"),
    ("앵콜", "앙코르"),
    ("로보트", "로봇"),
    ("바베큐", "바비큐"),
    ("부페", "뷔페"),
    ("초코렛", "초콜릿"),
    ("카페트", "카펫"),
    ("케잌", "케이크"),
    ("도너츠", "도넛"),
    ("슈퍼마켙", "슈퍼마켓"),
    ("써비스", "서비스"),
    ("센타", "센터"),
]
# 차별, 비하 표현 → 순화어(행정안전부 공문서 작성 지침, 국립국어원)
DISCRIM_FIXES = [
    ("장애자", "장애인"),
    ("장애우", "장애인"),
    ("불구자", "장애인"),
    ("정신박약", "지적장애"),
    ("정상인", "비장애인"),
    ("편부모", "한부모"),
    ("결손가정", "한부모가정"),
    ("미망인", "고인의 배우자"),
    ("학부형", "학부모"),
    ("불우이웃", "어려운 이웃"),
    ("유모차", "유아차"),
    ("저출산", "저출생"),
    ("잡상인", "이동상인"),
    ("파출부", "가사도우미"),
    ("청소부", "환경미화원"),
    ("간호원", "간호사"),
    ("운전수", "운전기사"),
    ("노가다", "건설노동자"),
    ("조선족", "중국동포"),
    ("매매춘", "성매매"),
    ("사생아", "혼외자"),
    ("벙어리", "언어장애인"),
    ("절름발이", "지체장애인"),
    ("애꾸눈", "시각장애인"),
    ("귀머거리", "청각장애인"),
]


def _alt(words):
    return re.compile(
        "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True))
    )


@dataclass
class Rule:
    code: str
    severity: str  # "error" | "warning"
    pattern: re.Pattern
    message: str
    suggest: str = ""
    skip_table: bool = False
    # 일치를 버릴지 정하는 추가 조건(길이가 바뀌는 뒤 보기 대신). (줄, 일치) → True 면 버림
    reject: Optional[Callable[[str, re.Match], bool]] = None


def _before(line: str, m: re.Match) -> str:
    return line[: m.start()]


# 법령 연혁 표기 <개정 2012.2.14>, 삭제 <2016.2.29.>, [시행일:2017.9.8.] 는 법제처 정본 형식이라 날짜 규칙에서 뺀다
_LAW_HISTORY = re.compile(
    r"(?:<(?:개정|신설|전문개정|전부개정|일부개정|제정)\s*|삭제\s*<|시행일\s*:\s*)$"
)
# 두음법칙: 숫자 뒤 1~3칸("2026 년도"), 괄호, 태그, 표 구분 뒤("( 년간)", "| 년도")는 기입란 접미라 뺀다
_DUEUM_REJECT_BEFORE = re.compile(r"(?:\d[ \t]{1,3}|[(（>|][ \t]*)$")

RULES: list[Rule] = [
    # 날짜: 온점 뒤 한 칸, 0 채움 금지, 연도 네 자리, 끝 마침표
    Rule(
        "DATE_NO_SPACE",
        "error",
        re.compile(r"\b\d{4}\.\d{1,2}\.\d{1,2}\.?"),
        "날짜 온점 뒤에 한 칸씩 띄워야 함",
        "예) 2025. 1. 6.",
        reject=lambda line, m: bool(_LAW_HISTORY.search(_before(line, m))),
    ),
    Rule(
        "DATE_ZERO_PAD",
        "error",
        re.compile(r"\b\d{4}\.\s*0\d\.|\b\d{4}\.\s*\d{1,2}\.\s*0\d"),
        "월, 일 앞의 '0'은 표기하지 않음",
        "예) 2025. 1. 6. (2025. 01. 06. ✕)",
    ),
    Rule(
        "DATE_2DIGIT_YR",
        "error",
        re.compile(r"(?<!\d)['’]\d{2}\.\s*\d"),
        "연도는 네 자리로 표기('24 ✕)",
        "예) 2025. 1. 6.",
    ),
    Rule(
        "DATE_NO_END_DOT",
        "warning",
        re.compile(r"\b\d{4}\.\s\d{1,2}\.\s\d{1,2}(?!\s*[.\d(])"),
        "날짜의 '일' 다음에 마침표(.)를 찍어야 함",
        "예) 2025. 1. 6.",
    ),
    # 하이픈 날짜(2026-07-18). URL, 파일명, 코드 안은 빼고 표 칸도 건너뛴다
    Rule(
        "DATE_HYPHEN",
        "warning",
        re.compile(r"(?<![/=&?#%.\w-])(?:19|20)\d{2}-\d{1,2}-\d{1,2}(?![/\w-])"),
        "날짜는 하이픈(-) 대신 온점으로 구분하고 온점 뒤 한 칸 띄움",
        "예) 2026. 7. 18.",
        skip_table=True,
    ),
    # 시간: 24시각제, 쌍점 붙여 쓰기
    Rule(
        "TIME_AMPM",
        "error",
        re.compile(r"(오전|오후|아침|밤|낮)\s*\d{1,2}\s*시"),
        "24시각제 숫자로 표기(오전/오후 사용 안 함)",
        "예) 09:00, 15:30",
    ),
    Rule(
        "TIME_24H",
        "warning",
        re.compile(r"(?<!\d)24\s*시(?!각)"),
        "'24시'보다 익일 00:00 또는 '18:00까지' 권장",
        "예) 18:00",
    ),
    Rule(
        "TIME_COLON_SP",
        "error",
        re.compile(r"\b\d{1,2}\s+:\s*\d{2}\b|\b\d{1,2}:\s+\d{2}\b"),
        "시와 분 사이 쌍점은 양쪽을 붙여 씀",
        "예) 13:20",
    ),
    # 금액: '천원' 금지, '금'과 숫자 붙여 쓰기
    Rule(
        "MONEY_CHEONWON",
        "error",
        re.compile(r"\d+\s*천\s*원"),
        "금액은 '천원'으로 줄이지 않고 아라비아 숫자로",
        "예) 345,000원",
    ),
    Rule(
        "MONEY_GEUM_SP",
        "warning",
        re.compile(r"금\s+\d"),
        "'금'과 숫자 사이는 붙여 쓰는 것이 원칙",
        "예) 금113,560원",
    ),
    # 붙임: 쌍점 금지(2타 띄움)
    Rule(
        "BUNIM_COLON",
        "error",
        re.compile(r"붙\s*임\s*:"),
        "'붙임' 다음에 쌍점(:)을 붙이지 않음(2타 띄움)",
        "예) 붙임  계획서 1부.",
    ),
    # 물결표와 '까지' 중복, 한글 먼저, 쌍점 띄어쓰기
    Rule(
        "KKAJI_DUP",
        "error",
        re.compile(r"[∼~～][^\n]{0,20}?까지"),
        "물결표(∼)와 '까지'를 함께 쓰지 않음",
        "예) 2. 20.∼2. 24.",
    ),
    Rule(
        "FOREIGN_FIRST",
        "warning",
        re.compile(r"\b[A-Z]{2,5}\s*\([가-힣]"),
        "한글을 먼저 쓰고 괄호 안에 외국어를 병기",
        "예) 업무 협약(MOU)",
    ),
    # 쌍점: 앞말에 붙이고 뒤는 한 칸. 주소(https://), 시각(13:20), 태그, 강조 닫힘은 제외. 표 칸은 서식 라벨이라 뺀다
    Rule(
        "COLON_SPACE",
        "warning",
        re.compile(r"\S\s+:(?!//)|\S:(?!//)[^\s\d<*_]"),
        "쌍점은 앞말에 붙이고 뒤는 한 칸 띄움",
        "예) 원장: 김갑동",
        skip_table=True,
    ),
    # 금액 한글 병기(시행규칙 제2조)
    Rule(
        "MONEY_NO_HANGUL",
        "warning",
        re.compile(r"금\d[\d,]*원(?![\s]*[(（])"),
        "금액은 숫자 다음 괄호 안에 한글 병기",
        "예) 금113,560원(금일십일만삼천오백육십원)",
    ),
    # 물결표 앞뒤 붙여 쓰기(숫자, 날짜, 시각 범위에만)
    Rule(
        "TILDE_SPACE",
        "warning",
        re.compile(r"(?<=[\d.)일월년시분’'])[ \t]+[∼~～]|[∼~～][ \t]+(?=[\d'’])"),
        "물결표(∼) 앞뒤는 붙여 씀",
        "예) 2. 20.∼2. 24., 09:00∼18:00",
    ),
    # 두음법칙: 어두의 '년도, 년간, 년말 …'은 '연도, 연간, 연말'
    Rule(
        "DUEUM_ERROR",
        "warning",
        re.compile(
            r"(?<![가-힣\d])(?<![ \t][ \t])년(?:도별|도|간|말|초|차|세|내)(?![가-힣])(?![ \t]*(?:</t[dh]>|\|))"
        ),
        "어두의 '년'은 두음법칙에 따라 '연'으로 적음",
        "예) 연도, 연간, 연말, 연초",
        reject=lambda line, m: bool(_DUEUM_REJECT_BEFORE.search(_before(line, m))),
    ),
    Rule(
        "LOANWORD_ERROR",
        "warning",
        _alt([w for w, _ in LOANWORD_FIXES]),
        "외래어 표기법에 맞지 않는 표기",
        "예) 콘텐츠, 애플리케이션, 메시지, 워크숍, 스케줄, 콘셉트",
    ),
    Rule(
        "DISCRIMINATORY_TERM",
        "warning",
        _alt([w for w, _ in DISCRIM_FIXES]),
        "차별, 비하 표현은 순화어로",
        "예) 장애자→장애인, 편부모→한부모, 학부형→학부모",
    ),
]


@dataclass
class Finding:
    line: int
    match: str
    rule: str
    severity: str
    message: str
    suggest: str


_DIGITS = "영일이삼사오육칠팔구"


def hangul_amount(text: str) -> str:
    """'금113,560원' 의 숫자를 한글로(일십일만삼천오백육십). 0 이면 '영'."""
    n = int(re.sub(r"\D", "", text) or 0)
    if n == 0:
        return "영"
    small = ["", "십", "백", "천"]
    big = ["", "만", "억", "조", "경"]
    out = []
    group = 0
    while n > 0:
        chunk = n % 10000
        if chunk:
            s = ""
            for i in range(3, -1, -1):
                d = (chunk // (10**i)) % 10
                if d:
                    s += _DIGITS[d] + small[i]
            out.append(s + big[group])
        n //= 10000
        group += 1
    return "".join(reversed(out))


def _suggest(rule: Rule, match: str) -> str:
    m = match.strip()
    if rule.code == "MONEY_NO_HANGUL":
        return f"{m} → {m}(금{hangul_amount(m)}원)"
    if rule.code == "DATE_HYPHEN":
        d = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", m)
        if d:
            return f"{m} → {d[1]}. {int(d[2])}. {int(d[3])}."
    table = (
        dict(LOANWORD_FIXES)
        if rule.code == "LOANWORD_ERROR"
        else dict(DISCRIM_FIXES)
        if rule.code == "DISCRIMINATORY_TERM"
        else None
    )
    if table and m in table:
        return f"{m} → {table[m]}"
    return rule.suggest


def lint_lines(
    lines: list[tuple[str, bool]], *, document: bool = False
) -> list[Finding]:
    """(줄, 표 칸 여부) 목록을 검사한다. 마크다운 펜스 코드 블록 안은 건너뛴다."""
    findings: list[Finding] = []
    fence: Optional[str] = None
    for i, (line, table_line) in enumerate(lines, 1):
        f = re.match(r"^\s*(```+|~~~+)", line)
        if f:
            kind = f.group(1)[0]
            if fence is None:
                fence = kind
            elif kind == fence:
                fence = None
            continue
        if fence is not None:
            continue
        table_line = (
            table_line
            or bool(re.match(r"^\s*\|", line))
            or bool(re.search(r"<t[dhr][\s>]", line, re.I))
        )
        for r in RULES:
            if r.skip_table and table_line:
                continue
            for m in r.pattern.finditer(line):
                if r.reject and r.reject(line, m):
                    continue
                findings.append(
                    Finding(
                        i,
                        m.group(0).strip(),
                        r.code,
                        r.severity,
                        r.message,
                        _suggest(r, m.group(0)),
                    )
                )
    if document:
        text = "\n".join(t for t, _ in lines)
        if re.search(r"^\s*붙\s*임(?![가-힣])", text, re.M) and not re.search(
            r"끝\.\s*$", text, re.M
        ):
            findings.append(
                Finding(
                    len(lines),
                    "붙임",
                    "END_MARK_MISSING",
                    "warning",
                    "붙임 표시 뒤에 '끝.' 표시가 없음",
                    "예) 붙임  계획서 1부.  끝.",
                )
            )
    return findings


def lint_text(text: str, *, document: bool = False) -> list[Finding]:
    """마크다운, 글을 검사한다(표는 `|` 줄로 알아본다)."""
    return lint_lines([(ln, False) for ln in text.splitlines()], document=document)


def hwpx_lines(path: str) -> list[tuple[str, bool]]:
    """hwpx 에서 본문 문단과 표 칸 문단을 뽑는다. 표 칸은 서식 라벨 규칙을 건너뛰게 표시한다."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from text_extract import extract_markdown  # 같은 폴더(스킬 내부)

    out: list[tuple[str, bool]] = []
    for ln in extract_markdown(path).splitlines():
        if ln.strip() == "---":
            continue
        out.append((ln.strip(), ln.startswith("  ")))
    return out


def format_findings(findings: list[Finding]) -> str:
    rows = [
        f'  L{f.line} [{f.severity}] {f.rule}: "{f.match}" — {f.message}'
        + (f" → {f.suggest}" if f.suggest else "")
        for f in findings
    ]
    err = sum(f.severity == "error" for f in findings)
    head = f"표기법 검수: 위반 {len(findings)}건 (error {err}, warning {len(findings) - err})"
    return "\n".join([head, *rows])


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="공문서 표기법 검수(행정업무운영 편람)")
    ap.add_argument("input", help="hwpx, md, txt 파일 또는 - (표준 입력)")
    ap.add_argument(
        "--document", action="store_true", help="붙임이 있으면 '끝.' 표시 확인"
    )
    a = ap.parse_args()
    if a.input == "-":
        findings = lint_text(sys.stdin.read(), document=a.document)
    elif a.input.lower().endswith(".hwpx"):
        findings = lint_lines(hwpx_lines(a.input), document=a.document)
    else:
        findings = lint_text(
            Path(a.input).read_text(encoding="utf-8"), document=a.document
        )
    print(format_findings(findings))
    return 1 if any(f.severity == "error" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
