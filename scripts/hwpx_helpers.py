#!/usr/bin/env python3
"""
HWPX 문서 생성 헬퍼 함수 라이브러리.

government 템플릿 기반의 표지 배너, 섹션 바, 본문, 이미지 등
검증된 빌드 패턴을 재사용 가능한 함수로 제공한다.

사용법:
    from hwpx_helpers import *
    # 또는
    exec(open("${CLAUDE_SKILL_DIR}/scripts/hwpx_helpers.py").read())
"""

import os
import re
import zipfile

MIME_MAP = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg",
    "png": "image/png", "bmp": "image/bmp", "gif": "image/gif",
}

# 빈 lineSegArray 가 들어 있는 paragraph 는 polaris-dvc 가 JID 11004 ("paragraph
# has text but empty lineSegArray") 로 잡는다. HwpOffice 는 알아서 보정해 열지만
# 후발 검증기·구현체 호환을 위해 기본 더미를 박아 둔다 — 한글이 다음 편집 시
# 자동으로 재계산하므로 시각적 영향 없음. (참조: PolarisOffice/polaris_dvc v0.1.0)
LINESEG_DUMMY = (
    '<hp:linesegarray><hp:lineseg textpos="0" vertpos="0" '
    'vertsize="900" textheight="900" baseline="765" spacing="360" '
    'horzpos="0" horzsize="22960" flags="393216"/></hp:linesegarray>'
)


def inject_dummy_linesegs(section_xml: str) -> tuple[str, int]:
    """linesegarray 가 없는 paragraph 에 더미를 박아 넣는다.

    `</hp:p>` 직전 위치에 단 1회만 삽입하며, 이미 linesegarray 가 존재하는
    paragraph 는 건드리지 않는다.

    [nested hp:p 안전]: HWPX 표는 외부 paragraph(hp:p) > hp:tbl > hp:tc > hp:subList
    > 내부 paragraph(hp:p) 형태로 nested된다. 단순 `(<hp:p>)(.*?)(</hp:p>)` 정규식은
    외부 시작 + 내부 닫기까지 매치되어 외부에 dummy linesegarray가 잘못 박힐 수 있다.
    `(?:(?!<hp:p\b).)*?` 부정 lookahead로 innermost paragraph만 매치하도록 보장.

    셀 내 줄바꿈을 paragraph 분리로 처리하는 다른 함수(예: hwpx_form_filler의
    `_set_cell_multi_paragraph`)도 같은 nested 함정을 가질 수 있으므로 string-기반
    조작 대신 lxml etree(:func:`ensure_dummy_linesegs_etree`)를 권장.

    Returns:
        (변환된 XML, 삽입된 paragraph 수)
    """
    # innermost <hp:p>만 매치 — 외부(표 포함) paragraph에 잘못 적용되지 않도록 보호
    pattern = re.compile(
        r"(<hp:p [^>]*>)((?:(?!<hp:p\b).)*?)(</hp:p>)", re.DOTALL
    )
    count = 0

    def repl(m: "re.Match[str]") -> str:
        nonlocal count
        body = m.group(2)
        if "<hp:linesegarray" in body:
            return m.group(0)
        count += 1
        return m.group(1) + body + LINESEG_DUMMY + m.group(3)

    new_xml = pattern.sub(repl, section_xml)
    return new_xml, count


def replace_placeholder_multiline(section_xml: str, key: str, value: str) -> str:
    """placeholder가 들어 있는 셀 paragraph를 multi-line value로 안전하게 치환.

    셀 내 줄바꿈을 paragraph 분리로 표현하려면 같은 hp:p를 라인 수만큼 복제해야
    한다. 단순 `<hp:p>[\\s\\S]*?</hp:p>` 정규식은 nested 구조(표 외부 paragraph가
    내부 셀 paragraph를 포함)에서 **외부+내부 둘 다 매치 → paragraph 곱셈 폭발**을
    일으킨다. (실측 사례: section0.xml 50KB → 244MB.)

    이 함수는 innermost hp:p만 매치하는 부정 lookahead로 그 폭발을 차단한다.

    [동작]
      - value에 \\n이 없으면 단순 string replace (xml escape 적용).
      - \\n이 있으면 placeholder가 들어 있는 hp:p를 lines 수만큼 복제, 각 줄을
        별도 paragraph 텍스트로.
      - placeholder가 hp:p 안에 없으면 fallback으로 \\n을 공백으로 합쳐 단순 치환.

    [한계]
      - 한 hp:p 안에 같은 multi-line placeholder가 두 번 이상 있으면 두 번째는
        그대로 남음. lxml 기반 셀 조작(:func:`_set_cell_multi_paragraph`)을 권장.

    Args:
        section_xml: Contents/section0.xml 문자열
        key: 치환 대상 placeholder (예: "{{교사활동}}")
        value: 채울 값 (\\n 줄바꿈 가능)

    Returns:
        치환 결과 XML
    """
    text = "" if value is None else str(value)
    lines = text.split("\n")

    def _xml_escape(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    if len(lines) == 1:
        return section_xml.replace(key, _xml_escape(text))

    escaped_key = re.escape(key)
    # innermost hp:p만 매치 (nested paragraph 폭발 방지)
    pattern = re.compile(
        r"<hp:p\b[^>]*>(?:(?!<hp:p\b).)*?"
        + escaped_key
        + r"(?:(?!<hp:p\b).)*?</hp:p>",
        re.DOTALL,
    )

    def repl(m: "re.Match[str]") -> str:
        match = m.group(0)
        return "".join(match.replace(key, _xml_escape(line)) for line in lines)

    new_xml, n = pattern.subn(repl, section_xml)
    if n == 0:
        # paragraph 매치 안 됨 — 줄바꿈을 공백으로 합쳐 fallback (silent data loss 경고)
        import warnings
        warnings.warn(
            f"replace_placeholder_multiline: '{key}' not found inside any innermost <hp:p>; "
            "falling back to inline replace (newlines lost).",
            stacklevel=2,
        )
        return section_xml.replace(key, _xml_escape(" ".join(lines)))
    return new_xml


def ensure_dummy_linesegs_etree(section_tree) -> int:
    """lxml etree 기반: 모든 `<hp:p>` 에 linesegarray 가 없으면 더미를 박는다.

    `hwpx_modifier`/`hwpx_form_filler` 처럼 etree 로 작업하는 파이프라인용.
    string-기반의 :func:`inject_dummy_linesegs` 와 효과 동일.

    Returns:
        삽입된 paragraph 수
    """
    from lxml import etree

    ns = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
    count = 0
    for p in section_tree.iter(f"{ns}p"):
        if p.find(f"{ns}linesegarray") is not None:
            continue
        seg_arr = etree.SubElement(p, f"{ns}linesegarray")
        etree.SubElement(
            seg_arr,
            f"{ns}lineseg",
            textpos="0", vertpos="0", vertsize="900",
            textheight="900", baseline="765", spacing="360",
            horzpos="0", horzsize="22960", flags="393216",
        )
        count += 1
    return count


# nested 안전 정규식 — innermost <hp:p> 만 매치 (inject_dummy_linesegs 와 동일 패턴)
_INNER_P_PATTERN = re.compile(
    r"<hp:p [^>]*>(?:(?!<hp:p\b).)*?</hp:p>", re.DOTALL
)
_LINESEG_PATTERN = re.compile(
    r"<hp:linesegarray\b[^>]*>.*?</hp:linesegarray>", re.DOTALL
)


def remove_linesegarray_in_paragraphs_matching(section_xml, predicate):
    """``predicate(block_xml)`` 가 True 인 hp:p 블록의 hp:linesegarray 제거.

    한글2018 같은 일부 구현체는 단락에 저장된 lineseg 캐시(vertpos, horzsize)
    를 그대로 따라가 자간 압축·점선 끊김·페이지번호 잘림 같은 시각 문제를
    일으킨다. lineseg 통째 제거 시 한글이 폰트 메트릭으로 자동 재계산하여
    정확한 위치로 그려진다.

    :func:`inject_dummy_linesegs` 와 **보완 관계** —
      * 빈 lineseg 단락 (polaris JID 11004 위반) → 더미 주입
      * 단일/잘못된 lineseg 캐시 (자간 압축, 점선 끊김) → 통째 제거

    Args:
        section_xml: ``Contents/section*.xml`` 문자열.
        predicate: ``(block_xml: str) -> bool``. True 면 그 hp:p 의 lineseg 제거.
            예시:
              * ``lambda b: 'leader="3"' in b`` — 목차 점선 단락만
              * ``lambda b: 'horzsize="49108"' in b`` — 단일 lineseg 단락만

    Returns:
        ``(수정된 XML, lineseg 가 제거된 단락 수)``.

    참조: public-doc-to-hwpx v3.6.5 ``fix_toc_dots.py::remove_linesegarray_from_dotted_paragraphs``
        (Kminer2053, MIT) 알고리즘 일반화. 원본 소스 코드는 포함하지 않음.
    """
    count = 0

    def repl(m):
        nonlocal count
        block = m.group(0)
        if not predicate(block):
            return block
        new_block = _LINESEG_PATTERN.sub("", block)
        if new_block != block:
            count += 1
        return new_block

    new_xml = _INNER_P_PATTERN.sub(repl, section_xml)
    return new_xml, count

# --- 네임스페이스 선언 (section0.xml 루트에 사용) ---
NS_DECL = (
    'xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app" '
    'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" '
    'xmlns:hp10="http://www.hancom.co.kr/hwpml/2016/paragraph" '
    'xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" '
    'xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core" '
    'xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" '
    'xmlns:hhs="http://www.hancom.co.kr/hwpml/2011/history" '
    'xmlns:hm="http://www.hancom.co.kr/hwpml/2011/master-page" '
    'xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf" '
    'xmlns:dc="http://purl.org/dc/elements/1.1/" '
    'xmlns:opf="http://www.idpf.org/2007/opf/" '
    'xmlns:ooxmlchart="http://www.hancom.co.kr/hwpml/2016/ooxmlchart" '
    'xmlns:hwpunitchar="http://www.hancom.co.kr/hwpml/2016/HwpUnitChar" '
    'xmlns:epub="http://www.idpf.org/2007/ops" '
    'xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0"'
)

# --- ID 카운터 ---
_id_counter = 0


def next_id():
    """문서 내 고유 ID 생성."""
    global _id_counter
    _id_counter += 1
    return str(_id_counter)


def reset_id(start=0):
    """ID 카운터 리셋."""
    global _id_counter
    _id_counter = start


def xml_escape(text):
    """XML 특수문자 이스케이프."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


# --- header.xml 검증 ---
def validate_header_for_government(header_path):
    """government 템플릿 header.xml인지 검증.
    charPr 81/82/83/144, borderFill 8~15를 사용하려면
    반드시 government header (335KB, 160+ charPr)가 필요하다.
    기본 header (60KB, 11 charPr)를 쓰면 서식이 깨진다.
    """
    import os
    size = os.path.getsize(header_path)
    if size < 100000:  # government header는 335KB
        raise ValueError(
            f"⚠️ header.xml이 너무 작습니다 ({size:,} bytes).\n"
            f"government 템플릿의 컬러 배너/섹션 바를 사용하려면\n"
            f"government header.xml (335KB)을 사용해야 합니다.\n"
            f"올바른 경로: $SKILL_DIR/templates/government/header.xml\n"
            f"현재 경로: {header_path}"
        )
    # charPr 개수 확인
    with open(header_path, "r", encoding="utf-8") as f:
        content = f.read(500)
    m = re.search(r'charProperties\s+itemCnt="(\d+)"', content)
    if m and int(m.group(1)) < 145:
        raise ValueError(
            f"⚠️ header.xml의 charPr가 {m.group(1)}개뿐입니다.\n"
            f"government 템플릿은 160+ charPr가 필요합니다 (charPr 144 사용).\n"
            f"올바른 header: $SKILL_DIR/templates/government/header.xml"
        )


# --- secPr 추출 ---
def extract_secpr_and_colpr(hwpx_path):
    """레퍼런스 HWPX에서 secPr + colPr 블록 추출."""
    with zipfile.ZipFile(hwpx_path, "r") as z:
        data = z.read("Contents/section0.xml").decode("utf-8")
    m = re.search(r"<hp:secPr.*?</hp:secPr>", data, re.DOTALL)
    secpr = m.group() if m else ""
    end = m.end() if m else 0
    ctrl_m = re.search(r"<hp:ctrl>.*?</hp:ctrl>", data[end:end + 500], re.DOTALL)
    colpr = ctrl_m.group() if ctrl_m else ""
    return secpr, colpr


# --- 기본 문단 생성 ---
def make_first_para(secpr, colpr, charpr="25", parapr="40"):
    """첫 문단 (secPr + colPr 포함, 필수)."""
    p_id = next_id()
    return (
        f'<hp:p id="{p_id}" paraPrIDRef="{parapr}" styleIDRef="0" '
        f'pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="{charpr}">'
        f'{secpr}{colpr}'
        f'</hp:run></hp:p>'
    )


def make_empty_line(charpr="41", parapr="18"):
    """빈 줄."""
    p_id = next_id()
    return (
        f'<hp:p id="{p_id}" paraPrIDRef="{parapr}" styleIDRef="0" '
        f'pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="{charpr}"><hp:t/></hp:run></hp:p>'
    )


def make_page_break(charpr="41", parapr="18"):
    """강제 페이지 넘김."""
    p_id = next_id()
    return (
        f'<hp:p id="{p_id}" paraPrIDRef="{parapr}" styleIDRef="0" '
        f'pageBreak="1" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="{charpr}"><hp:t/></hp:run></hp:p>'
    )


def make_text_para(text, charpr, parapr):
    """텍스트 문단."""
    p_id = next_id()
    return (
        f'<hp:p id="{p_id}" paraPrIDRef="{parapr}" styleIDRef="0" '
        f'pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="{charpr}"><hp:t>{xml_escape(text)}</hp:t></hp:run></hp:p>'
    )


def make_body_para(marker, text, marker_charpr="18", text_charpr="38", parapr="4"):
    """본문 문단: 볼드 마커 + 일반 내용. (예: "가. 내용텍스트")"""
    p_id = next_id()
    return (
        f'<hp:p id="{p_id}" paraPrIDRef="{parapr}" styleIDRef="0" '
        f'pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="{marker_charpr}"><hp:t>{xml_escape(f"  {marker} ")}</hp:t></hp:run>'
        f'<hp:run charPrIDRef="{text_charpr}"><hp:t>{xml_escape(text)}</hp:t></hp:run></hp:p>'
    )


# --- 표지 배너 (3×2 컬러 테이블) ---
def make_cover_banner(title_text, title_charpr="144", title_parapr="20",
                      bf_top=("10", "8"), bf_bottom=("9", "11"), bf_title="15"):
    """
    표지 배너: 3행 2열 테이블.
    1행: 컬러 바 (좌: bf_top[0], 우: bf_top[1])
    2행: 제목 (colspan=2, bf=bf_title)
    3행: 컬러 바 (좌: bf_bottom[0], 우: bf_bottom[1])
    """
    table_width = 47624
    half_width = 23812
    thin_h = 382
    title_h = 7410
    total_h = thin_h + title_h + thin_h

    tbl_id = next_id()
    p_id = next_id()

    def thin_cell(col, row, bf, w):
        cid = next_id()
        return (
            f'<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="1" borderFillIDRef="{bf}">'
            f'<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" '
            f'linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">'
            f'<hp:p paraPrIDRef="2" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0" id="{cid}">'
            f'<hp:run charPrIDRef="42"><hp:t/></hp:run></hp:p>'
            f'</hp:subList>'
            f'<hp:cellAddr colAddr="{col}" rowAddr="{row}"/>'
            f'<hp:cellSpan colSpan="1" rowSpan="1"/>'
            f'<hp:cellSz width="{w}" height="{thin_h}"/>'
            f'<hp:cellMargin left="0" right="0" top="0" bottom="0"/></hp:tc>'
        )

    title_cid = next_id()
    title_cell = (
        f'<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="1" borderFillIDRef="{bf_title}">'
        f'<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" '
        f'linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">'
        f'<hp:p paraPrIDRef="{title_parapr}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0" id="{title_cid}">'
        f'<hp:run charPrIDRef="{title_charpr}"><hp:t>{xml_escape(title_text)}</hp:t></hp:run></hp:p>'
        f'</hp:subList>'
        f'<hp:cellAddr colAddr="0" rowAddr="1"/>'
        f'<hp:cellSpan colSpan="2" rowSpan="1"/>'
        f'<hp:cellSz width="{table_width}" height="{title_h}"/>'
        f'<hp:cellMargin left="283" right="283" top="141" bottom="141"/></hp:tc>'
    )

    return (
        f'<hp:p id="{p_id}" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="0">'
        f'<hp:tbl id="{tbl_id}" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" '
        f'textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="0" '
        f'rowCnt="3" colCnt="2" cellSpacing="0" borderFillIDRef="4" noAdjust="0">'
        f'<hp:sz width="{table_width}" widthRelTo="ABSOLUTE" height="{total_h}" heightRelTo="ABSOLUTE" protect="0"/>'
        f'<hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" '
        f'holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" '
        f'vertOffset="0" horzOffset="0"/>'
        f'<hp:outMargin left="0" right="0" top="0" bottom="0"/>'
        f'<hp:inMargin left="0" right="0" top="0" bottom="0"/>'
        f'<hp:tr>{thin_cell(0, 0, bf_top[0], half_width)}{thin_cell(1, 0, bf_top[1], half_width)}</hp:tr>'
        f'<hp:tr>{title_cell}</hp:tr>'
        f'<hp:tr>{thin_cell(0, 2, bf_bottom[0], half_width)}{thin_cell(1, 2, bf_bottom[1], half_width)}</hp:tr>'
        f'</hp:tbl></hp:run></hp:p>'
    )


# --- 섹션 바 (1×3 컬러 테이블) ---
def make_section_bar(number, title, num_charpr="81", gap_charpr="82", title_charpr="83",
                     bf_num="14", bf_gap="13", bf_title="12"):
    """
    섹션 바: 1행 3열.
    Cell 0: 번호 (파랑), Cell 1: 간격 (회색), Cell 2: 제목 (하늘색)
    """
    # 제목 길이에 따라 Cell 2 너비 계산
    korean = sum(1 for ch in title if ord(ch) > 0x7F)
    ascii_c = len(title) - korean
    cell2_width = korean * 2200 + ascii_c * 1100 + 4000

    cell0_width = 3422
    cell1_width = 565
    table_width = cell0_width + cell1_width + cell2_width

    p_id = next_id()
    tbl_id = next_id()
    p0_id = next_id()
    p1_id = next_id()
    p2_id = next_id()

    return (
        f'<hp:p id="{p_id}" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="0">'
        f'<hp:tbl id="{tbl_id}" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" '
        f'textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="0" '
        f'rowCnt="1" colCnt="3" cellSpacing="0" borderFillIDRef="4" noAdjust="0">'
        f'<hp:sz width="{table_width}" widthRelTo="ABSOLUTE" height="3027" heightRelTo="ABSOLUTE" protect="0"/>'
        f'<hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" '
        f'holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" '
        f'horzAlign="LEFT" vertOffset="0" horzOffset="0"/>'
        f'<hp:outMargin left="0" right="0" top="0" bottom="0"/>'
        f'<hp:inMargin left="0" right="0" top="0" bottom="0"/>'
        f'<hp:tr>'
        # Cell 0: 번호
        f'<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="1" borderFillIDRef="{bf_num}">'
        f'<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" '
        f'linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">'
        f'<hp:p paraPrIDRef="21" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0" id="{p0_id}">'
        f'<hp:run charPrIDRef="{num_charpr}"><hp:t>{xml_escape(number)}</hp:t></hp:run></hp:p>'
        f'</hp:subList>'
        f'<hp:cellAddr colAddr="0" rowAddr="0"/><hp:cellSpan colSpan="1" rowSpan="1"/>'
        f'<hp:cellSz width="{cell0_width}" height="3027"/>'
        f'<hp:cellMargin left="141" right="141" top="141" bottom="141"/></hp:tc>'
        # Cell 1: 간격
        f'<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="1" borderFillIDRef="{bf_gap}">'
        f'<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" '
        f'linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">'
        f'<hp:p paraPrIDRef="2" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0" id="{p1_id}">'
        f'<hp:run charPrIDRef="{gap_charpr}"><hp:t/></hp:run></hp:p>'
        f'</hp:subList>'
        f'<hp:cellAddr colAddr="1" rowAddr="0"/><hp:cellSpan colSpan="1" rowSpan="1"/>'
        f'<hp:cellSz width="{cell1_width}" height="3027"/>'
        f'<hp:cellMargin left="141" right="141" top="141" bottom="141"/></hp:tc>'
        # Cell 2: 제목
        f'<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="1" borderFillIDRef="{bf_title}">'
        f'<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" '
        f'linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">'
        f'<hp:p paraPrIDRef="2" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0" id="{p2_id}">'
        f'<hp:run charPrIDRef="{title_charpr}"><hp:t> {xml_escape(title)}</hp:t></hp:run></hp:p>'
        f'</hp:subList>'
        f'<hp:cellAddr colAddr="2" rowAddr="0"/><hp:cellSpan colSpan="1" rowSpan="1"/>'
        f'<hp:cellSz width="{cell2_width}" height="3027"/>'
        f'<hp:cellMargin left="141" right="141" top="141" bottom="141"/></hp:tc>'
        f'</hp:tr></hp:tbl></hp:run></hp:p>'
    )


# --- 이미지 문단 ---
def make_image_para(binary_item_id, width=40000, height=22500, parapr="19"):
    """
    이미지 문단. 전체 hp:pic 필수 구조 포함.
    width, height: HWPUNIT 단위 (기본 16:9 = 40000×22500).
    """
    p_id = next_id()
    pic_id = next_id()
    inst_id = next_id()
    cx, cy = width // 2, height // 2
    return (
        f'<hp:p id="{p_id}" paraPrIDRef="{parapr}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="0">'
        f'<hp:pic id="{pic_id}" zOrder="0" numberingType="PICTURE" '
        f'textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" '
        f'href="" groupLevel="0" instid="{inst_id}" reverse="0">'
        f'<hp:offset x="0" y="0"/>'
        f'<hp:orgSz width="{width}" height="{height}"/>'
        f'<hp:curSz width="{width}" height="{height}"/>'
        f'<hp:flip horizontal="0" vertical="0"/>'
        f'<hp:rotationInfo angle="0" centerX="{cx}" centerY="{cy}" rotateimage="0"/>'
        f'<hp:renderingInfo>'
        f'<hc:transMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/>'
        f'<hc:scaMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/>'
        f'<hc:rotMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/>'
        f'</hp:renderingInfo>'
        f'<hc:img binaryItemIDRef="{binary_item_id}" bright="0" contrast="0" effect="REAL_PIC" alpha="0"/>'
        f'<hp:imgRect>'
        f'<hc:pt0 x="0" y="0"/><hc:pt1 x="{width}" y="0"/>'
        f'<hc:pt2 x="{width}" y="{height}"/><hc:pt3 x="0" y="{height}"/>'
        f'</hp:imgRect>'
        f'<hp:imgClip left="0" right="{width}" top="0" bottom="{height}"/>'
        f'<hp:inMargin left="0" right="0" top="0" bottom="0"/>'
        f'<hp:imgDim dimwidth="{width}" dimheight="{height}"/>'
        f'<hp:effects/>'
        f'<hp:sz width="{width}" widthRelTo="ABSOLUTE" height="{height}" heightRelTo="ABSOLUTE" protect="0"/>'
        f'<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0" '
        f'holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="CENTER" '
        f'vertOffset="0" horzOffset="0"/>'
        f'<hp:outMargin left="0" right="0" top="0" bottom="0"/>'
        f'</hp:pic><hp:t/></hp:run></hp:p>'
    )


# --- 표지 페이지 어셈블리 ---
def make_cover_page(title, subtitle="", date="", subtitle_charpr="62", subtitle_parapr="52",
                    date_charpr="60", date_parapr="1"):
    """표지 페이지 전체 생성: 빈줄 + 배너 + 부제 + 날짜 + pageBreak."""
    parts = []
    for _ in range(6):
        parts.append(make_empty_line())
    parts.append(make_cover_banner(title))
    if subtitle:
        parts.append(make_empty_line())
        parts.append(make_text_para(subtitle, charpr=subtitle_charpr, parapr=subtitle_parapr))
    for _ in range(8):
        parts.append(make_empty_line())
    if date:
        parts.append(make_text_para(date, charpr=date_charpr, parapr=date_parapr))
    for _ in range(4):
        parts.append(make_empty_line())
    parts.append(make_page_break())
    return parts


# --- 이미지 ZIP 추가 ---
def add_images_to_hwpx(hwpx_path, images):
    """images: [{"file": "photo.jpg", "id": "img1", "src_path": "/abs/path"}]"""
    tmp = str(hwpx_path) + ".img_tmp"
    with zipfile.ZipFile(hwpx_path, "r") as zin:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "mimetype":
                    zout.writestr(item, data, compress_type=zipfile.ZIP_STORED)
                else:
                    zout.writestr(item, data)
            for img in images:
                zout.write(img["src_path"], f"BinData/{img['file']}")
    os.replace(tmp, str(hwpx_path))


def update_content_hpf(hwpx_path, images):
    """content.hpf에 이미지 항목 등록."""
    tmp = str(hwpx_path) + ".hpf_tmp"
    with zipfile.ZipFile(hwpx_path, "r") as zin:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "Contents/content.hpf":
                    text = data.decode("utf-8")
                    items = ""
                    for img in images:
                        ext = img["file"].rsplit(".", 1)[-1].lower()
                        mime = MIME_MAP.get(ext, "image/png")
                        items += (f'<opf:item id="{img["id"]}" '
                                  f'href="BinData/{img["file"]}" '
                                  f'media-type="{mime}" isEmbeded="1"/>')
                    text = text.replace("</opf:manifest>", items + "</opf:manifest>")
                    data = text.encode("utf-8")
                if item.filename == "mimetype":
                    zout.writestr(item, data, compress_type=zipfile.ZIP_STORED)
                else:
                    zout.writestr(item, data)
    os.replace(tmp, str(hwpx_path))


def insert_image_at(hwpx_path, img_path, anchor_text, width_mm=120,
                    position="before", parapr="0", output_path=None):
    """
    이미지를 anchor_text가 포함된 문단 앞/뒤에 인라인 삽입한다.
    4단계(ZIP추가+hpf등록+pic생성+재패킹)를 단일 호출로 처리.

    Args:
        hwpx_path: 대상 HWPX 파일 경로
        img_path: 삽입할 이미지 파일 경로
        anchor_text: 삽입 위치를 결정하는 텍스트 (이 텍스트가 포함된 문단 앞/뒤)
        width_mm: 이미지 표시 폭 (mm, 기본 120mm). 높이는 비율 자동 계산.
        position: "before" (문단 앞) 또는 "after" (문단 뒤)
        parapr: 이미지 문단의 paraPrIDRef (기본 "0")
        output_path: 출력 경로. None이면 원본 덮어쓰기.
    """
    import re
    from PIL import Image

    hwpx_path = str(hwpx_path)
    img_path = str(img_path)
    out = output_path or hwpx_path

    with Image.open(img_path) as im:
        w_px, h_px = im.size
    w_hu = int(width_mm * 283.5)
    h_hu = int(w_hu * h_px / w_px)

    fname = os.path.basename(img_path)
    img_id = fname.rsplit(".", 1)[0]

    with zipfile.ZipFile(hwpx_path, "r") as zin:
        section = zin.read("Contents/section0.xml").decode("utf-8")
        hpf = zin.read("Contents/content.hpf").decode("utf-8")

        pic_xml = make_image_para(img_id, width=w_hu, height=h_hu, parapr=parapr)

        match = re.search(re.escape(anchor_text), section)
        if not match:
            raise ValueError(f"anchor_text '{anchor_text}' not found in section0.xml")

        if position == "before":
            p_start = section.rfind("<hp:p", 0, match.start())
            section = section[:p_start] + pic_xml + "\n" + section[p_start:]
        else:
            p_end = section.find("</hp:p>", match.end()) + len("</hp:p>")
            section = section[:p_end] + "\n" + pic_xml + section[p_end:]

        ext = fname.rsplit(".", 1)[-1].lower()
        mime = MIME_MAP.get(ext, "image/png")
        hpf_item = (f'<opf:item id="{img_id}" href="BinData/{fname}" '
                    f'media-type="{mime}" isEmbeded="1"/>')
        hpf = hpf.replace("</opf:manifest>", hpf_item + "</opf:manifest>")

        tmp = out + ".tmp"
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == "Contents/section0.xml":
                    zout.writestr(item, section.encode("utf-8"))
                elif item.filename == "Contents/content.hpf":
                    zout.writestr(item, hpf.encode("utf-8"))
                elif item.filename == "mimetype":
                    zout.writestr(item, zin.read(item.filename),
                                  compress_type=zipfile.ZIP_STORED)
                else:
                    zout.writestr(item, zin.read(item.filename))
            zout.write(img_path, f"BinData/{fname}")

    os.replace(tmp, out)


# =============================================================================
# rhwp 기반 헬퍼 (edwardkim/rhwp, MIT License 참조)
# =============================================================================

def local_name(tag):
    """lxml 태그에서 네임스페이스 접두사를 제거한 로컬 이름을 반환한다.

    rhwp `src/parser/hwpx/utils.rs:10-18` 패턴 차용.
    HWPX XML은 ``hp:``, ``hc:``, ``hs:`` 등 다양한 prefix가 혼재하므로
    ``elem.tag == "{uri}p"`` 비교 대신 ``local_name(elem.tag) == "p"`` 를 쓰면 견고하다.

    Args:
        tag: lxml `_Element.tag` 문자열. ``"{http://...}p"`` 또는 ``"hp:p"`` 또는 ``"p"``.

    Returns:
        로컬 이름 (예: ``"p"``).
    """
    if not isinstance(tag, str):
        return ""
    if tag.startswith("{"):
        # Clark notation: {uri}localname
        end = tag.find("}")
        return tag[end + 1:] if end >= 0 else tag
    if ":" in tag:
        return tag.split(":", 1)[1]
    return tag


def xpath_local(root, local_name_pattern):
    """로컬 이름 기반 XPath 검색. 네임스페이스 접두사 무관.

    Args:
        root: lxml `_Element` 루트.
        local_name_pattern: 로컬 이름 (예: ``"p"``) 또는 계층(예: ``"tbl/tr/tc"``).

    Returns:
        매칭된 `_Element` 리스트.

    예시::

        for p in xpath_local(root, "p"):          # 모든 <hp:p>
            ...
        for t in xpath_local(root, "tbl//t"):     # <hp:tbl> 하위의 모든 <hp:t>
            ...
    """
    parts = [p for p in local_name_pattern.split("/") if p != ""]
    axis = "descendant::"
    query_parts = []
    for part in parts:
        if part == "":  # "//" (빈 파트) — descendant axis
            axis = "descendant-or-self::"
            continue
        query_parts.append(f"{axis}*[local-name()='{part}']")
        axis = "descendant-or-self::"
    return root.xpath("/".join(query_parts))


def utf16_len(s):
    """UTF-16 코드 유닛 길이.

    HWP 바이너리 포맷은 char_offset을 UTF-16 코드 유닛 단위로 계산한다.
    대부분의 한글·ASCII는 1 코드 유닛이지만, 이모지·일부 한자(surrogate pair)는
    2 코드 유닛이다. Python `len(s)`는 코드포인트 기준이라 어긋날 수 있다.

    rhwp `src/parser/hwpx/section.rs:299-322` 참조.

    Args:
        s: 문자열.

    Returns:
        UTF-16 코드 유닛 수.

    예시::

        utf16_len("가")      # 1  (BMP)
        utf16_len("a")       # 1
        utf16_len("\U0001F600")  # 2  (U+1F600, surrogate pair)
    """
    return len(s.encode("utf-16-le")) // 2


def tab_aware_offset(s, tab_width=8):
    """탭 문자를 N 코드 유닛으로 확장한 UTF-16 오프셋.

    HWP 바이너리에서 탭 컨트롤 문자(0x0009)는 8 UTF-16 코드 유닛으로 계산된다.
    문자열에 탭이 포함된 문단의 char_shape 경계를 계산할 때 필요하다.

    rhwp `src/parser/hwpx/section.rs:310-322` 참조.

    Args:
        s: 문자열.
        tab_width: 탭당 코드 유닛 수 (기본 8).

    Returns:
        탭 확장 후 UTF-16 오프셋.
    """
    if "\t" not in s:
        return utf16_len(s)
    total = 0
    for ch in s:
        if ch == "\t":
            total += tab_width
        elif ord(ch) > 0xFFFF:
            total += 2  # surrogate pair
        else:
            total += 1
    return total


# zip bomb 방어 상한 (rhwp src/parser/hwpx/reader.rs:19-26)
HWPX_MAX_XML_SIZE = 32 * 1024 * 1024       # 32 MB — content.hpf, section*.xml, header.xml 등
HWPX_MAX_BINDATA_SIZE = 64 * 1024 * 1024   # 64 MB — BinData/*.png, .jpg 등


def read_zip_entry_limited(zf, name, *, limit=None):
    """zip bomb 방어 상한을 적용한 zip 엔트리 읽기.

    압축 해제된 크기가 ``limit`` 을 초과하면 예외 발생. 기본 상한은 파일 경로에서
    추론: BinData/* 는 64MB, 나머지는 32MB.

    Args:
        zf: ``zipfile.ZipFile`` 객체.
        name: 엔트리 이름.
        limit: 사용자 지정 상한 (bytes). None이면 자동 결정.

    Raises:
        ValueError: 상한 초과.

    Returns:
        bytes.
    """
    info = zf.getinfo(name)
    if limit is None:
        limit = HWPX_MAX_BINDATA_SIZE if name.startswith("BinData/") else HWPX_MAX_XML_SIZE
    if info.file_size > limit:
        raise ValueError(
            f"zip 엔트리 크기 초과 ({name}: {info.file_size} > {limit}). zip bomb 가능성."
        )
    data = zf.read(name)
    if len(data) > limit:  # ZipInfo.file_size가 거짓일 수 있어 실제 크기로도 검증
        raise ValueError(f"압축 해제 후 크기 초과 ({name}: {len(data)} > {limit})")
    return data


# =============================================================================
# HWPX FORMULA 필드 주입 (HwpOffice 실스펙 검증, 2026-04-19)
# =============================================================================
#
# HwpOffice 가 직접 저장하는 FORMULA 필드는 다음 구조다 (한컴 실파일 역공학):
#
#   <hp:run charPrIDRef="...">
#     <hp:ctrl>
#       <hp:fieldBegin id type="FORMULA" name editable dirty zorder fieldid metaTag>
#         <hp:parameters cnt="5" name="">
#           <hp:integerParam name="Prop">8</hp:integerParam>
#           <hp:stringParam name="Command">수식??포맷;;결과</hp:stringParam>
#           <hp:stringParam name="Formula">수식</hp:stringParam>
#           <hp:stringParam name="ResultFormat">%g,</hp:stringParam>
#           <hp:stringParam name="LastResult">결과</hp:stringParam>
#         </hp:parameters>
#       </hp:fieldBegin>
#     </hp:ctrl>
#     <hp:t>결과</hp:t>
#     <hp:ctrl><hp:fieldEnd beginIDRef fieldid/></hp:ctrl>
#     <hp:t/>
#   </hp:run>
#
# 핵심:
#   - <hp:ctrl> 래퍼 필수 (run 의 직접 자식이 아님)
#   - parameters cnt="5", Prop(integer)=8 고정
#   - Command 문자열은 "<formula>??<format>;;<result>" 레거시 패킹
#   - fieldEnd 속성은 beginIDRef/fieldid (fieldType 아님)
#   - 수식은 와일드카드 `?` 사용: =SUM(B?:E?) — ?=현재 행, =SUM(?2:?4) — ?=현재 열
#   - HwpOffice F9 (필드 업데이트) 로 재계산 가능
#
# 검증: HwpOffice에서 SUM/AVERAGE/MAX/MIN 정상 렌더·재계산 확인 (2026-04-18).


FORMULA_DEFAULT_FIELDID = 627469685   # 문서 내 FORMULA 필드 그룹 ID (HwpOffice 기본값)
FORMULA_DEFAULT_FORMAT = "%g,"        # 결과 포맷 (천 단위 콤마)


def build_formula_run_inner_xml(field_id, formula, result_str, *,
                                 fieldid=FORMULA_DEFAULT_FIELDID,
                                 result_format=FORMULA_DEFAULT_FORMAT):
    """FORMULA 필드 한 셀에 들어갈 <hp:run> 내부 XML 문자열을 생성한다.

    이 문자열을 기존 run 의 자식으로 이식하면 HwpOffice 호환 FORMULA 필드가 된다.

    Args:
        field_id: 필드별 유니크 ID (정수). 보통 `2139727780 + 순번` 사용.
        formula: 수식 문자열 (예: ``"=SUM(B?:E?)"``). 와일드카드 `?` 지원.
        result_str: 프리컴퓨트된 결과 문자열 (예: ``"5,710"``).
        fieldid: 문서 내 FORMULA 필드 그룹 ID (모든 필드가 공유).
        result_format: HwpOffice 결과 포맷 문자열 (기본 ``"%g,"``).

    Returns:
        run 내부에 넣을 XML 문자열 (ctrl + fieldBegin + t + ctrl + fieldEnd + t).
    """
    command = f"{formula}??{result_format};;{result_str}"
    return (
        '<hp:ctrl>'
        f'<hp:fieldBegin id="{field_id}" type="FORMULA" name="" '
        f'editable="0" dirty="0" zorder="-1" fieldid="{fieldid}" metaTag="">'
        '<hp:parameters cnt="5" name="">'
        '<hp:integerParam name="Prop">8</hp:integerParam>'
        f'<hp:stringParam name="Command">{command}</hp:stringParam>'
        f'<hp:stringParam name="Formula">{formula}</hp:stringParam>'
        f'<hp:stringParam name="ResultFormat">{result_format}</hp:stringParam>'
        f'<hp:stringParam name="LastResult">{result_str}</hp:stringParam>'
        '</hp:parameters>'
        '</hp:fieldBegin>'
        '</hp:ctrl>'
        f'<hp:t>{result_str}</hp:t>'
        '<hp:ctrl>'
        f'<hp:fieldEnd beginIDRef="{field_id}" fieldid="{fieldid}"/>'
        '</hp:ctrl>'
        '<hp:t/>'
    )


def apply_formula_to_cell(tc, field_id, formula, result_str, *,
                           fieldid=FORMULA_DEFAULT_FIELDID,
                           result_format=FORMULA_DEFAULT_FORMAT):
    """lxml ``<hp:tc>`` 셀에 FORMULA 필드를 주입한다.

    셀의 첫 run 자식들을 제거하고 새 FORMULA 필드 구조로 교체한다.
    셀에 ``dirty="1"`` 속성도 설정한다 (HwpOffice가 수식 셀로 인식).

    Args:
        tc: lxml `<hp:tc>` 엘리먼트 (네임스페이스 무관).
        field_id: 유니크 필드 ID.
        formula: 수식 문자열 (와일드카드 ``?`` 지원).
        result_str: 프리컴퓨트된 결과 문자열.
        fieldid: 필드 그룹 ID (문서 공통).
        result_format: 결과 포맷.

    Returns:
        bool — 성공하면 True. 셀에 <hp:run> 이 없으면 False.

    Example::

        from lxml import etree
        from hwpx_helpers import apply_formula_to_cell
        # tc = 어떤 <hp:tc> 엘리먼트
        apply_formula_to_cell(tc, 2139727780, "=SUM(B?:E?)", "5,710")
    """
    from lxml import etree as _et  # 지연 임포트 (lxml 미설치 환경 고려)

    HP_NS = "http://www.hancom.co.kr/hwpml/2011/paragraph"
    HP_RUN = f"{{{HP_NS}}}run"

    tc.set("dirty", "1")
    run = next(iter(tc.iter(HP_RUN)), None)
    if run is None:
        return False
    charPr = run.get("charPrIDRef", "0")
    for child in list(run):
        run.remove(child)

    inner = build_formula_run_inner_xml(
        field_id, formula, result_str,
        fieldid=fieldid, result_format=result_format,
    )
    new_run = _et.fromstring(
        f'<hp:run xmlns:hp="{HP_NS}" charPrIDRef="{charPr}">{inner}</hp:run>'
    )
    for child in new_run:
        run.append(child)
    return True


# --- 단위 변환 (HWPX HWPUNIT 체계) -----------------------------------
#
# HWPX 의 길이는 두 가지 단위가 혼재한다:
#   * HWPUNIT  = 1/7200 인치 ≈ 1/100 pt. 1 pt = 100, 1 mm ≈ 283.5
#   * 테두리/여백 일부는 사람이 읽는 "0.12 mm" 형태 문자열로 저장됨
# 사용자 코드는 mm·pt 단위로 받아 내부에서 HWPUNIT 으로 변환한다.

HWPUNIT_PER_MM = 283.464566929  # 7200 / 25.4
HWPUNIT_PER_PT = 100


def mm_to_hwpunit(mm: float) -> int:
    """밀리미터를 HWPUNIT(1/7200 inch) 정수로 변환."""
    return int(round(float(mm) * HWPUNIT_PER_MM))


def pt_to_hwpunit(pt: float) -> int:
    """포인트를 HWPUNIT 정수로 변환 (1pt = 100 HWPUNIT)."""
    return int(round(float(pt) * HWPUNIT_PER_PT))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """``(218, 229, 243)`` → ``"#DAE5F3"`` (HWPX 색상 표기)."""
    return "#{:02X}{:02X}{:02X}".format(int(r) & 0xFF, int(g) & 0xFF, int(b) & 0xFF)


# --- 셀 테두리/배경 borderFill 빌더 -----------------------------------
#
# HWPX 의 셀 시각 속성(테두리·배경)은 모두 header.xml 의 `<hh:borderFill>` 풀에
# 등록된 다음 셀(`<hp:tc>`)이 ``borderFillIDRef`` 로 참조한다. 같은 외형은 동일
# borderFill 을 공유해야 파일이 부풀지 않는다.
#
# 본 모듈은 단일 borderFill XML 문자열을 만드는 빌더만 제공한다. 풀 등록·dedup·
# id 부여는 :class:`HwpxModifier` 의 ``_register_border_fill`` 이 담당한다.

# 표준 테두리 변형. (type, width) 튜플.
BORDER_NONE     = ("NONE",        "0.1 mm")
BORDER_SOLID    = ("SOLID",       "0.12 mm")
BORDER_THICK    = ("SOLID",       "0.4 mm")    # 굵은 실선
BORDER_DOTTED   = ("DOT",         "0.12 mm")
BORDER_DASHED   = ("DASH",        "0.12 mm")
BORDER_DOUBLE   = ("DOUBLE_SLIM", "0.4 mm")    # sample.hwpx 에서 실측

DEFAULT_BORDER_COLOR = "#000000"


def _border_spec(side_spec):
    """``side_spec`` 정규화. None → BORDER_NONE, 문자열·튜플 모두 허용.

    허용 형태:
      * None / "none"           → 투명
      * "solid" / "thick" / "dotted" / "dashed" / "double"  → 표준 변형
      * (type, width)           → 직접 지정. width 는 ``"0.12 mm"`` 형식 문자열
      * (type, width, color)    → 색까지 직접 지정
    """
    if side_spec is None:
        return BORDER_NONE + (DEFAULT_BORDER_COLOR,)
    if isinstance(side_spec, str):
        key = side_spec.lower()
        return {
            "none":    BORDER_NONE,
            "solid":   BORDER_SOLID,
            "thick":   BORDER_THICK,
            "dotted":  BORDER_DOTTED,
            "dashed":  BORDER_DASHED,
            "double":  BORDER_DOUBLE,
        }[key] + (DEFAULT_BORDER_COLOR,)
    if isinstance(side_spec, tuple):
        if len(side_spec) == 2:
            return tuple(side_spec) + (DEFAULT_BORDER_COLOR,)
        if len(side_spec) == 3:
            return tuple(side_spec)
    raise ValueError(f"Invalid border spec: {side_spec!r}")


def build_border_fill_xml(
    border_id,
    *,
    left=None, right=None, top=None, bottom=None,
    border_color=None,
    bg_rgb=None,
):
    """단일 ``<hh:borderFill>`` 문자열 생성.

    Args:
        border_id: borderFill id (정수 또는 문자열).
        left/right/top/bottom: 변별 (:func:`_border_spec` 참조). 미지정 시 NONE.
        border_color: 4면 일괄 색상. ``"#193657"`` 또는 ``(25,54,87)``. 변별 자체에
            색이 들어 있으면 그게 우선.
        bg_rgb: 셀 배경. ``(r,g,b)`` 또는 ``"#DAE5F3"``. None 이면 fillBrush 생략.

    Returns:
        ``<hh:borderFill>...</hh:borderFill>`` 문자열 (네임스페이스 prefix 포함).
    """
    if isinstance(border_color, tuple):
        border_color = rgb_to_hex(*border_color)
    if border_color is None:
        border_color = DEFAULT_BORDER_COLOR

    sides = {}
    for name, raw in (("left", left), ("right", right),
                      ("top", top), ("bottom", bottom)):
        btype, bwidth, bcolor = _border_spec(raw)
        if isinstance(raw, tuple) and len(raw) == 3:
            color = bcolor
        else:
            color = border_color if btype != "NONE" else DEFAULT_BORDER_COLOR
        sides[name] = (btype, bwidth, color)

    parts = [
        f'<hh:borderFill id="{border_id}" threeD="0" shadow="0"'
        ' centerLine="NONE" breakCellSeparateLine="0">',
        '<hh:slash type="NONE" Crooked="0" isCounter="0"/>',
        '<hh:backSlash type="NONE" Crooked="0" isCounter="0"/>',
    ]
    for name in ("left", "right", "top", "bottom"):
        btype, bwidth, bcolor = sides[name]
        parts.append(
            f'<hh:{name}Border type="{btype}" width="{bwidth}" color="{bcolor}"/>'
        )
    parts.append('<hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/>')

    if bg_rgb is not None:
        if isinstance(bg_rgb, tuple):
            bg_hex = rgb_to_hex(*bg_rgb)
        else:
            bg_hex = bg_rgb
        parts.append(
            '<hc:fillBrush>'
            f'<hc:winBrush faceColor="{bg_hex}" hatchColor="#000000" alpha="0"/>'
            '</hc:fillBrush>'
        )
    parts.append('</hh:borderFill>')
    return "".join(parts)


# --- charPr 미세 변형 (장평·자간·진하게·기울임·글자색) ---------------
#
# HWPX charPr 의 핵심 자식 요소:
#   <hh:ratio   hangul="100" ...>   # 장평 (가로 배율 %, woo773 `장평`)
#   <hh:spacing hangul="0"   ...>   # 자간 (% — 음수 = 좁게, woo773 `자간`)
#   <hh:bold/>                       # 진하게 (요소 존재 = 활성)
#   <hh:italic/>                     # 기울임
#   <hh:underline type="SOLID"/>     # 밑줄 (type 이 NONE 외이면 활성)
#   textColor 속성                   # 글자색
#
# 같은 base_id 에서 동일 변형이면 같은 새 id 를 재사용한다 (dedup).


def charpr_variant_signature(base_id, *, width=None, letter_spacing=None,
                             bold=None, italic=None, underline=None,
                             text_color=None):
    """charPr 변형 dedup 키. ``HwpxModifier._register_charpr_variant`` 가 사용."""
    if isinstance(text_color, tuple):
        text_color = rgb_to_hex(*text_color)
    return (str(base_id), width, letter_spacing, bold, italic, underline, text_color)


def apply_charpr_variant(charpr_elem, *, width=None, letter_spacing=None,
                         bold=None, italic=None, underline=None, text_color=None):
    """주어진 ``<hh:charPr>`` 요소(deepcopy 본)에 변형을 in-place 적용한다.

    None 으로 둔 인자는 원본 값을 유지한다.

    Args:
        charpr_elem: lxml 의 ``<hh:charPr>`` 요소 (이미 복제된 사본)
        width: 장평. 50~200 범위의 백분율 정수. (woo773 `장평(95)` 와 동일)
        letter_spacing: 자간. -50 ~ 50 범위의 백분율 정수.
            (woo773 `자간(-12)` → letter_spacing=-12)
        bold: True/False/None. None 이면 변경 없음.
        italic: True/False/None.
        underline: True/False/None. True 면 SOLID 밑줄.
        text_color: ``(r,g,b)`` 또는 ``"#RRGGBB"``. None 이면 변경 없음.
    """
    HH = "{http://www.hancom.co.kr/hwpml/2011/head}"
    LANGS = ("hangul", "latin", "hanja", "japanese", "other", "symbol", "user")

    if width is not None:
        ratio = charpr_elem.find(f"{HH}ratio")
        if ratio is not None:
            for lang in LANGS:
                ratio.set(lang, str(width))

    if letter_spacing is not None:
        spacing = charpr_elem.find(f"{HH}spacing")
        if spacing is not None:
            for lang in LANGS:
                spacing.set(lang, str(letter_spacing))

    if bold is not None:
        bold_el = charpr_elem.find(f"{HH}bold")
        if bold and bold_el is None:
            from lxml import etree as _et
            _et.SubElement(charpr_elem, f"{HH}bold")
        elif (not bold) and bold_el is not None:
            charpr_elem.remove(bold_el)

    if italic is not None:
        italic_el = charpr_elem.find(f"{HH}italic")
        if italic and italic_el is None:
            from lxml import etree as _et
            _et.SubElement(charpr_elem, f"{HH}italic")
        elif (not italic) and italic_el is not None:
            charpr_elem.remove(italic_el)

    if underline is not None:
        un_el = charpr_elem.find(f"{HH}underline")
        if un_el is not None:
            un_el.set("type", "SOLID" if underline else "NONE")

    if text_color is not None:
        if isinstance(text_color, tuple):
            text_color = rgb_to_hex(*text_color)
        charpr_elem.set("textColor", text_color)


def border_fill_signature(
    *,
    left=None, right=None, top=None, bottom=None,
    border_color=None,
    bg_rgb=None,
):
    """동일 borderFill 재사용을 위한 hashable 키.

    `_register_border_fill` 의 dedup 캐시 키로 사용. 같은 시각 속성이면 같은 id 를
    공유하도록 한다.
    """
    if isinstance(border_color, tuple):
        border_color = rgb_to_hex(*border_color)
    if isinstance(bg_rgb, tuple):
        bg_rgb = rgb_to_hex(*bg_rgb)
    return (
        _border_spec(left),
        _border_spec(right),
        _border_spec(top),
        _border_spec(bottom),
        border_color,
        bg_rgb,
    )
