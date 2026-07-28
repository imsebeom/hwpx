#!/usr/bin/env python3
"""
마크다운 → HWPX 변환기 (md2hwpx)

마크다운 파일을 파싱하여 HWPX section0.xml을 생성하고,
build_hwpx.py를 통해 완성된 HWPX 문서를 만든다.

Usage:
    python md2hwpx.py input.md -o output.hwpx
    python md2hwpx.py input.md -o output.hwpx --template report
    python md2hwpx.py input.md -o output.hwpx --template report --header custom_header.xml
    python md2hwpx.py input.md -o output.hwpx --title "문서 제목" --creator "작성자"

마크다운 → HWPX 스타일 매핑 (report 템플릿 기준):
    # 제목       → charPrIDRef=7 (20pt 볼드), paraPrIDRef=20 (가운데)
    ## 섹션      → charPrIDRef=8 (14pt 볼드), paraPrIDRef=0
    ### 소제목   → charPrIDRef=13 (12pt 볼드 돋움), paraPrIDRef=27 (섹션헤더 테두리)
    #### 하위    → charPrIDRef=10 (10pt 볼드+밑줄), paraPrIDRef=0
    본문         → charPrIDRef=0 (10pt 바탕), paraPrIDRef=0
    **볼드**     → charPrIDRef=9 (10pt 볼드)
    > 인용       → charPrIDRef=11 (9pt), paraPrIDRef=24 (들여쓰기)
    - 목록       → charPrIDRef=0, paraPrIDRef=24 (들여쓰기)
      - 하위목록 → charPrIDRef=0, paraPrIDRef=25 (깊은 들여쓰기)
    1. 번호목록  → charPrIDRef=0, paraPrIDRef=24
"""

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape
from hwpx_helpers import NS_DECL

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent

# ─── 스타일 매핑 프로파일 ───────────────────────────────────────

STYLE_PROFILES = {
    "report": {
        "title":        {"charPr": "7",  "paraPr": "20"},  # 20pt 볼드, 가운데
        "h2":           {"charPr": "8",  "paraPr": "0"},   # 14pt 볼드
        "h3":           {"charPr": "13", "paraPr": "27"},  # 12pt 볼드 돋움, 섹션헤더
        "h4":           {"charPr": "10", "paraPr": "0"},   # 10pt 볼드+밑줄
        "h5":           {"charPr": "9",  "paraPr": "0"},   # 10pt 볼드
        "h6":           {"charPr": "0",  "paraPr": "0"},   # 10pt 일반 (본문과 동일)
        "body":         {"charPr": "0",  "paraPr": "0"},   # 10pt 바탕
        "bold":         {"charPr": "9"},                    # 10pt 볼드
        "italic":       {"charPr": "0"},                    # 이탤릭 (charPr 0 기반, 텍스트로 구분)
        "underline":    {"charPr": "0"},                    # 밑줄
        "strikethrough":{"charPr": "0"},                    # 취소선
        "small":        {"charPr": "11", "paraPr": "0"},   # 9pt
        "quote":        {"charPr": "11", "paraPr": "24"},  # 9pt, 들여쓰기
        "list_l1":      {"charPr": "0",  "paraPr": "24"},  # 들여쓰기 1
        "list_l2":      {"charPr": "0",  "paraPr": "25"},  # 들여쓰기 2
        "list_l3":      {"charPr": "0",  "paraPr": "26"},  # 들여쓰기 3
        "table_header": {"charPr": "9",  "paraPr": "21"},  # 볼드, 표 가운데
        "table_cell":   {"charPr": "0",  "paraPr": "22"},  # 표 본문
    },
    "gonmun": {
        "title":        {"charPr": "7",  "paraPr": "20"},
        "h2":           {"charPr": "8",  "paraPr": "0"},
        "h3":           {"charPr": "10", "paraPr": "0"},
        "h4":           {"charPr": "0",  "paraPr": "0"},
        "h5":           {"charPr": "10", "paraPr": "0"},
        "h6":           {"charPr": "0",  "paraPr": "0"},
        "body":         {"charPr": "0",  "paraPr": "0"},
        "bold":         {"charPr": "10"},
        "italic":       {"charPr": "0"},
        "underline":    {"charPr": "0"},
        "strikethrough":{"charPr": "0"},
        "small":        {"charPr": "9",  "paraPr": "0"},
        "quote":        {"charPr": "9",  "paraPr": "0"},
        "list_l1":      {"charPr": "0",  "paraPr": "0"},
        "list_l2":      {"charPr": "0",  "paraPr": "0"},
        "list_l3":      {"charPr": "0",  "paraPr": "0"},
        "table_header": {"charPr": "10", "paraPr": "21"},
        "table_cell":   {"charPr": "0",  "paraPr": "22"},
    },
    "base": {
        "title":        {"charPr": "3",  "paraPr": "0"},
        "h2":           {"charPr": "3",  "paraPr": "0"},
        "h3":           {"charPr": "0",  "paraPr": "0"},
        "h4":           {"charPr": "0",  "paraPr": "0"},
        "h5":           {"charPr": "0",  "paraPr": "0"},
        "h6":           {"charPr": "0",  "paraPr": "0"},
        "body":         {"charPr": "0",  "paraPr": "0"},
        "bold":         {"charPr": "0"},
        "italic":       {"charPr": "0"},
        "underline":    {"charPr": "0"},
        "strikethrough":{"charPr": "0"},
        "small":        {"charPr": "0",  "paraPr": "0"},
        "quote":        {"charPr": "0",  "paraPr": "0"},
        "list_l1":      {"charPr": "0",  "paraPr": "0"},
        "list_l2":      {"charPr": "0",  "paraPr": "0"},
        "list_l3":      {"charPr": "0",  "paraPr": "0"},
        "table_header": {"charPr": "0",  "paraPr": "0"},
        "table_cell":   {"charPr": "0",  "paraPr": "0"},
    },
}

# minutes와 proposal은 report와 유사한 매핑
STYLE_PROFILES["minutes"] = STYLE_PROFILES["report"].copy()
STYLE_PROFILES["proposal"] = STYLE_PROFILES["report"].copy()

# ─── secPr 템플릿 (첫 문단에 포함) ─────────────────────────────

SECPR_TEMPLATE = """<hp:secPr id="" textDirection="HORIZONTAL" spaceColumns="1134" tabStop="8000" tabStopVal="4000" tabStopUnit="HWPUNIT" outlineShapeIDRef="1" memoShapeIDRef="0" textVerticalWidthHead="0" masterPageCnt="0">
        <hp:grid lineGrid="0" charGrid="0" wonggojiFormat="0"/>
        <hp:startNum pageStartsOn="BOTH" page="0" pic="0" tbl="0" equation="0"/>
        <hp:visibility hideFirstHeader="0" hideFirstFooter="0" hideFirstMasterPage="0" border="SHOW_ALL" fill="SHOW_ALL" hideFirstPageNum="0" hideFirstEmptyLine="0" showLineNumber="0"/>
        <hp:lineNumberShape restartType="0" countBy="0" distance="0" startNumber="0"/>
        <hp:pagePr landscape="WIDELY" width="59528" height="84186" gutterType="LEFT_ONLY">
          <hp:margin header="4252" footer="4252" gutter="0" left="8504" right="8504" top="5668" bottom="4252"/>
        </hp:pagePr>
        <hp:footNotePr>
          <hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" supscript="0"/>
          <hp:noteLine length="-1" type="SOLID" width="0.12 mm" color="#000000"/>
          <hp:noteSpacing betweenNotes="283" belowLine="567" aboveLine="850"/>
          <hp:numbering type="CONTINUOUS" newNum="1"/>
          <hp:placement place="EACH_COLUMN" beneathText="0"/>
        </hp:footNotePr>
        <hp:endNotePr>
          <hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" supscript="0"/>
          <hp:noteLine length="14692344" type="SOLID" width="0.12 mm" color="#000000"/>
          <hp:noteSpacing betweenNotes="0" belowLine="567" aboveLine="850"/>
          <hp:numbering type="CONTINUOUS" newNum="1"/>
          <hp:placement place="END_OF_DOCUMENT" beneathText="0"/>
        </hp:endNotePr>
        <hp:pageBorderFill type="BOTH" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0" fillArea="PAPER">
          <hp:offset left="1417" right="1417" top="1417" bottom="1417"/>
        </hp:pageBorderFill>
        <hp:pageBorderFill type="EVEN" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0" fillArea="PAPER">
          <hp:offset left="1417" right="1417" top="1417" bottom="1417"/>
        </hp:pageBorderFill>
        <hp:pageBorderFill type="ODD" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0" fillArea="PAPER">
          <hp:offset left="1417" right="1417" top="1417" bottom="1417"/>
        </hp:pageBorderFill>
      </hp:secPr>
      <hp:ctrl>
        <hp:colPr id="" type="NEWSPAPER" layout="LEFT" colCount="1" sameSz="1" sameGap="0"/>
      </hp:ctrl>"""


# ─── XML 생성 헬퍼 ──────────────────────────────────────────────

class SectionBuilder:
    """section0.xml을 구성하는 빌더."""

    def __init__(self, profile: dict):
        self.profile = profile
        self.paragraphs: list[str] = []
        self._next_id = 1000000001
        self._first_para = True
        # 동일 헤더 구조를 가진 표들의 열 너비 재사용 캐시
        self._table_widths_cache: dict[tuple, list[int]] = {}

    def _get_id(self) -> str:
        pid = str(self._next_id)
        self._next_id += 1
        return pid

    def _make_para(self, text: str, style_key: str, runs: list[tuple[str, str]] | None = None) -> str:
        """단일 문단 XML 생성.

        Args:
            text: 본문 텍스트 (runs가 None일 때 사용)
            style_key: 스타일 프로파일 키
            runs: [(charPrIDRef, text), ...] 형태의 런 목록 (혼합 서식용)
        """
        style = self.profile.get(style_key, self.profile["body"])
        char_pr = style["charPr"]
        para_pr = style.get("paraPr", "0")
        pid = self._get_id()

        # 첫 문단에는 secPr 포함
        if self._first_para:
            self._first_para = False
            return f'''  <hp:p id="{pid}" paraPrIDRef="{para_pr}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
    <hp:run charPrIDRef="{char_pr}">
      {SECPR_TEMPLATE}
    </hp:run>
    <hp:run charPrIDRef="{char_pr}">
      <hp:t>{xml_escape(text)}</hp:t>
    </hp:run>
  </hp:p>'''

        if runs:
            run_xml = "\n    ".join(
                f'<hp:run charPrIDRef="{cpr}"><hp:t>{xml_escape(t)}</hp:t></hp:run>'
                for cpr, t in runs
            )
            return f'''  <hp:p id="{pid}" paraPrIDRef="{para_pr}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
    {run_xml}
  </hp:p>'''

        return f'''  <hp:p id="{pid}" paraPrIDRef="{para_pr}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
    <hp:run charPrIDRef="{char_pr}">
      <hp:t>{xml_escape(text)}</hp:t>
    </hp:run>
  </hp:p>'''

    def add_empty_line(self):
        """빈 줄 추가."""
        pid = self._get_id()
        if self._first_para:
            self._first_para = False
            self.paragraphs.append(f'''  <hp:p id="{pid}" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
    <hp:run charPrIDRef="0">
      {SECPR_TEMPLATE}
    </hp:run>
    <hp:run charPrIDRef="0"><hp:t/></hp:run>
  </hp:p>''')
        else:
            self.paragraphs.append(f'''  <hp:p id="{pid}" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
    <hp:run charPrIDRef="0"><hp:t/></hp:run>
  </hp:p>''')

    def add_paragraph(self, text: str, style_key: str = "body"):
        """일반 문단 추가."""
        self.paragraphs.append(self._make_para(text, style_key))

    def add_mixed_paragraph(self, runs: list[tuple[str, str]], style_key: str = "body"):
        """혼합 서식 문단 추가. runs: [(style_key, text), ...]"""
        style = self.profile.get(style_key, self.profile["body"])
        para_pr = style.get("paraPr", "0")
        resolved_runs = []
        for sk, t in runs:
            s = self.profile.get(sk, self.profile["body"])
            resolved_runs.append((s["charPr"], t))
        pid = self._get_id()
        if self._first_para:
            self._first_para = False
            first_cpr = resolved_runs[0][0] if resolved_runs else "0"
            run_xml = "\n    ".join(
                f'<hp:run charPrIDRef="{cpr}"><hp:t>{xml_escape(t)}</hp:t></hp:run>'
                for cpr, t in resolved_runs
            )
            self.paragraphs.append(f'''  <hp:p id="{pid}" paraPrIDRef="{para_pr}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
    <hp:run charPrIDRef="{first_cpr}">
      {SECPR_TEMPLATE}
    </hp:run>
    {run_xml}
  </hp:p>''')
        else:
            run_xml = "\n    ".join(
                f'<hp:run charPrIDRef="{cpr}"><hp:t>{xml_escape(t)}</hp:t></hp:run>'
                for cpr, t in resolved_runs
            )
            self.paragraphs.append(f'''  <hp:p id="{pid}" paraPrIDRef="{para_pr}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
    {run_xml}
  </hp:p>''')

    def add_table(self, headers: list[str], rows: list[list[str]]):
        """표 추가. 열 너비는 내용 길이에 비례하여 자동 배분."""
        num_cols = len(headers)
        num_rows = 1 + len(rows)  # 헤더 + 데이터
        body_width = 42520
        MIN_COL_WIDTH = 2800  # 최소 열 너비 (~10mm)

        # 열별 최대 텍스트 길이 계산 (한글=2, ASCII=1 가중치)
        def text_weight(s: str) -> float:
            w = 0
            for ch in s:
                if ord(ch) > 0x7F:
                    w += 2
                else:
                    w += 1
            return max(w, 1)

        def split_cell_lines(text: str) -> list:
            """셀 텍스트를 여러 줄로 분할 (표 셀 내 개조식 렌더링).
            1) <br>/<br/>/<br /> 명시적 줄바꿈 지원
            2) 중간 위치의 bullet 기호(◦ ○ ● • ▪ ∘) 앞에서 자동 줄바꿈
            3) 하위 항목 " - " 앞에서 자동 줄바꿈(들여쓰기 2칸 유지)
            """
            import re
            t = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
            t = re.sub(r'(?<!^)(?<!\n)\s+(?=[◦○●•▪∘])', '\n', t)
            t = re.sub(r'(?<!^)(?<!\n) - (?=\S)', '\n  - ', t)
            lines = [ln.rstrip() for ln in t.split('\n') if ln.strip()]
            return lines if lines else [text]

        # 한글 10pt 가중치당 520 HWPUNIT + 셀 마진 좌우 566 + 줄끝 여유 280
        NO_WRAP_THRESHOLD = 14  # 한글 7자 — 데이터 셀 줄바꿈 없음 보장 임계
        CELL_PAD = 566 + 280
        CHAR_UNIT = 520
        def required_width(line_weight):
            return line_weight * CHAR_UNIT + CELL_PAD

        col_weights = []
        col_min_widths = []
        for ci in range(num_cols):
            max_w = text_weight(headers[ci])
            header_w = text_weight(headers[ci])
            # 헤더는 길이에 관계없이 반드시 한 줄 보장
            short_candidates = [MIN_COL_WIDTH, required_width(header_w)]
            # 데이터 셀 내 임계 이하인 줄도 한 줄 보장
            for row in rows:
                if ci < len(row):
                    cell = row[ci]
                    max_w = max(max_w, text_weight(cell))
                    for line in split_cell_lines(cell):
                        lw = text_weight(line)
                        if lw <= NO_WRAP_THRESHOLD:
                            short_candidates.append(required_width(lw))
            col_weights.append(max_w)
            col_min_widths.append(max(short_candidates))

        total_weight = sum(col_weights)
        col_widths = [max(col_min_widths[ci], int(body_width * col_weights[ci] / total_weight)) for ci in range(num_cols)]

        # 총합을 body_width에 맞춤
        total = sum(col_widths)
        if total > body_width:
            # 초과 시 비례 축소 (각 열 MIN_COL_WIDTH 보장)
            ratio = body_width / total
            col_widths = [max(MIN_COL_WIDTH, int(w * ratio)) for w in col_widths]
            diff = body_width - sum(col_widths)
            if diff != 0:
                idx = col_widths.index(max(col_widths))
                col_widths[idx] += diff
        elif total < body_width:
            # 부족 시 가장 넓은 열에 추가
            widest = col_widths.index(max(col_widths))
            col_widths[widest] += (body_width - total)

        # 동일 헤더 구조 + 유사한 데이터 크기 분포 표가 반복되면 열 너비를 통일
        # col_weights를 구간화(S/M/L/XL)해서 키의 일부로 사용 → 성격이 다른 표는 별개
        def _bucket(w):
            if w <= 10: return 'S'
            if w <= 30: return 'M'
            if w <= 100: return 'L'
            return 'XL'
        cache_key = (tuple(headers), tuple(_bucket(w) for w in col_weights))
        if cache_key in self._table_widths_cache:
            col_widths = list(self._table_widths_cache[cache_key])
        else:
            self._table_widths_cache[cache_key] = list(col_widths)

        row_height = 2400

        # 표를 담는 문단
        pid = self._get_id()
        tbl_id = self._get_id()

        total_height = row_height * num_rows

        BULLET_CHARS = ('◦', '○', '●', '•', '▪', '∘', '-')
        header_profile = self.profile.get("table_header", self.profile["body"])
        center_para_pr = header_profile.get("paraPr", "0")

        def make_cell(text: str, is_header: bool, col_idx: int, row_idx: int,
                      row_span: int = 1) -> str:
            bf = "4" if is_header else "3"
            cp = self.profile.get("table_header" if is_header else "table_cell", self.profile["body"])
            char_pr = cp["charPr"]
            default_para_pr = cp.get("paraPr", "0")
            lines = split_cell_lines(text)
            # 가운데 정렬 조건: 줄바꿈 없음(한 줄) + 글머리 기호 시작 아님
            has_bullet = any(ln.lstrip().startswith(BULLET_CHARS) for ln in lines)
            use_center = is_header or (len(lines) == 1 and not has_bullet)
            para_pr = center_para_pr if use_center else default_para_pr
            paras = []
            for line in lines:
                cell_pid = self._get_id()
                paras.append(
                    f'            <hp:p paraPrIDRef="{para_pr}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0" id="{cell_pid}">\n'
                    f'              <hp:run charPrIDRef="{char_pr}"><hp:t>{xml_escape(line)}</hp:t></hp:run>\n'
                    f'            </hp:p>'
                )
            paras_xml = "\n".join(paras)
            cell_height = row_height * row_span
            return f'''        <hp:tc name="" header="{1 if is_header else 0}" hasMargin="1" protect="0" editable="0" dirty="1" borderFillIDRef="{bf}">
          <hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">
{paras_xml}
          </hp:subList>
          <hp:cellAddr colAddr="{col_idx}" rowAddr="{row_idx}"/>
          <hp:cellSpan colSpan="1" rowSpan="{row_span}"/>
          <hp:cellSz width="{col_widths[col_idx]}" height="{cell_height}"/>
          <hp:cellMargin left="283" right="283" top="142" bottom="142"/>
        </hp:tc>'''

        # 헤더 행
        header_cells = "\n".join(make_cell(h, True, i, 0) for i, h in enumerate(headers))
        header_row = f"      <hp:tr>\n{header_cells}\n      </hp:tr>"

        # 데이터 행 — 셀 값이 '^' 또는 '^^'이면 위 셀과 rowSpan 병합
        # (빈 셀은 그냥 빈 셀. 병합은 명시적 토큰으로만.)
        MERGE_UP_TOKENS = {'^', '^^'}
        # cell_rowspan[ri][ci] = 해당 셀의 rowSpan, 0이면 병합 흡수되어 XML 생략
        cell_rowspan = [[1] * num_cols for _ in range(len(rows))]
        main_row_for_col = [None] * num_cols  # 각 열의 마지막 주 셀 행
        for ri, row in enumerate(rows):
            for ci in range(num_cols):
                val = row[ci] if ci < len(row) else ''
                if val.strip() in MERGE_UP_TOKENS and main_row_for_col[ci] is not None:
                    # 병합: 위 주 셀 rowSpan++, 현재 셀 스킵
                    cell_rowspan[main_row_for_col[ci]][ci] += 1
                    cell_rowspan[ri][ci] = 0
                else:
                    main_row_for_col[ci] = ri

        data_rows = []
        for ri, row in enumerate(rows):
            padded = row + [""] * (num_cols - len(row))
            cell_xmls = []
            for ci in range(num_cols):
                rs = cell_rowspan[ri][ci]
                if rs == 0:
                    continue  # 병합 흡수 셀 XML 생략
                cell_xmls.append(make_cell(padded[ci], False, ci, ri + 1, rs))
            data_rows.append(f"      <hp:tr>\n" + "\n".join(cell_xmls) + f"\n      </hp:tr>")

        all_rows = header_row + "\n" + "\n".join(data_rows)

        if self._first_para:
            self._first_para = False
            secpr_part = f"""    <hp:run charPrIDRef="0">
      {SECPR_TEMPLATE}
    </hp:run>"""
        else:
            secpr_part = ""

        tbl_xml = f'''  <hp:p id="{pid}" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
{secpr_part}
    <hp:run charPrIDRef="0">
      <hp:tbl id="{tbl_id}" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="0" rowCnt="{num_rows}" colCnt="{num_cols}" cellSpacing="0" borderFillIDRef="3" noAdjust="0">
        <hp:sz width="{body_width}" widthRelTo="ABSOLUTE" height="{total_height}" heightRelTo="AT_LEAST" protect="0"/>
        <hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>
        <hp:outMargin left="0" right="0" top="0" bottom="0"/>
        <hp:inMargin left="0" right="0" top="0" bottom="0"/>
{all_rows}
      </hp:tbl>
    </hp:run>
  </hp:p>'''
        self.paragraphs.append(tbl_xml)

    def build_xml(self) -> str:
        """완성된 section0.xml 문자열 반환."""
        from hwpx_helpers import inject_dummy_linesegs
        body = "\n".join(self.paragraphs)
        body = self._unify_table_widths(body)
        body, _ = inject_dummy_linesegs(body)
        return f'''<?xml version='1.0' encoding='UTF-8'?>
<hs:sec {NS_DECL}>
{body}
</hs:sec>'''

    @staticmethod
    def _unify_table_widths(body: str) -> str:
        """같은 헤더 구조의 표들은 열 너비를 그룹별 최대값으로 통일."""
        from collections import defaultdict
        tbl_pat = re.compile(r'<hp:tbl[^>]*>.*?</hp:tbl>', re.DOTALL)
        tc_pat = re.compile(r'<hp:tc[^>]*>.*?</hp:tc>', re.DOTALL)

        # 그룹: headers tuple -> [(start, end, widths), ...]
        groups = defaultdict(list)
        for m in tbl_pat.finditer(body):
            tbl = m.group()
            col_m = re.search(r'colCnt="(\d+)"', tbl)
            if not col_m:
                continue
            nc = int(col_m.group(1))
            tcs = tc_pat.findall(tbl)
            if len(tcs) < nc:
                continue
            headers = []
            widths = []
            for tc in tcs[:nc]:
                ts = re.findall(r'<hp:t>([^<]+)</hp:t>', tc)
                headers.append(ts[0] if ts else '')
                w = re.search(r'<hp:cellSz width="(\d+)"', tc)
                widths.append(int(w.group(1)) if w else 0)
            groups[tuple(headers)].append((m.start(), m.end(), widths))

        # 그룹별 max 너비 (합이 body_width 초과 시 비례 축소)
        BODY_WIDTH = 42520
        MIN_COL = 2800
        max_widths = {}
        for key, items in groups.items():
            if len(items) < 2:
                continue
            nc = len(items[0][2])
            unified = [max(it[2][i] for it in items) for i in range(nc)]
            total = sum(unified)
            if total > BODY_WIDTH:
                # 각 열을 최소 너비 보장하며 비례 축소
                ratio = BODY_WIDTH / total
                unified = [max(MIN_COL, int(w * ratio)) for w in unified]
                # 반올림 오차·MIN 보정으로 생긴 diff를 가장 큰 열에 흡수
                diff = BODY_WIDTH - sum(unified)
                if diff != 0:
                    idx = unified.index(max(unified))
                    unified[idx] += diff
            max_widths[key] = unified

        if not max_widths:
            return body

        # 뒤에서부터 치환 (인덱스 밀림 방지)
        all_updates = []
        for key, items in groups.items():
            if key not in max_widths:
                continue
            unified = max_widths[key]
            for start, end, _ in items:
                all_updates.append((start, end, unified))
        all_updates.sort(key=lambda x: -x[0])

        cell_sz_pat = re.compile(r'<hp:cellSz width="\d+"')
        for start, end, unified in all_updates:
            tbl_xml = body[start:end]
            col_m = re.search(r'colCnt="(\d+)"', tbl_xml)
            if not col_m:
                continue
            nc = int(col_m.group(1))
            idx = [0]
            def repl(m, nc=nc, unified=unified, idx=idx):
                w = unified[idx[0] % nc]
                idx[0] += 1
                return f'<hp:cellSz width="{w}"'
            new_tbl = cell_sz_pat.sub(repl, tbl_xml)
            body = body[:start] + new_tbl + body[end:]

        return body


# ─── 마크다운 파서 ───────────────────────────────────────────────

_INLINE_PATTERN = re.compile(
    r'\*\*(.+?)\*\*'                          # **bold**
    r'|(?<!\*)\*(?!\*)(.+?)\*(?!\*)'          # *italic* (not **)
    r'|~~(.+?)~~'                             # ~~strikethrough~~
    r'|<u>(.+?)</u>'                          # <u>underline</u>
)


def parse_inline_bold(text: str) -> list[tuple[str, str]]:
    """**볼드**, *이탤릭*, ~~취소선~~, <u>밑줄</u> 마크다운을 분리.
    [(style_key, text), ...] 반환. style_key: body, bold, italic, underline, strikethrough
    주의: italic/underline/strikethrough는 파싱되지만, 현재 charPr "0"(본문)으로 출력됨.
    header.xml에 해당 charPr 추가 시 시각적 구분 가능."""
    tokens = []
    last = 0
    for m in _INLINE_PATTERN.finditer(text):
        if m.start() > last:
            tokens.append(("body", text[last:m.start()]))
        if m.group(1):
            tokens.append(("bold", m.group(1)))
        elif m.group(2):
            tokens.append(("italic", m.group(2)))
        elif m.group(3):
            tokens.append(("strikethrough", m.group(3)))
        elif m.group(4):
            tokens.append(("underline", m.group(4)))
        last = m.end()
    if last < len(text):
        tokens.append(("body", text[last:]))
    return tokens if tokens else [("body", text)]


def strip_markdown_formatting(text: str) -> str:
    """인라인 마크다운 문법 제거 (볼드, 이탤릭, 링크 등)."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'[\1]', text)
    return text


def parse_markdown_table(lines: list[str]) -> tuple[list[str], list[list[str]]]:
    """마크다운 파이프 테이블 파싱. (headers, rows) 반환."""
    if len(lines) < 2:
        return [], []
    header_line = lines[0].strip().strip('|')
    headers = [h.strip() for h in header_line.split('|')]

    rows = []
    for line in lines[2:]:  # separator (lines[1]) 건너뛰기
        row_line = line.strip().strip('|')
        cells = [strip_markdown_formatting(c.strip()) for c in row_line.split('|')]
        rows.append(cells)

    return [strip_markdown_formatting(h) for h in headers], rows


def md_to_section(md_text: str, template: str = "report") -> tuple[str, str]:
    """마크다운 텍스트를 section0.xml로 변환.

    Returns:
        (section_xml, title) 튜플
    """
    profile = STYLE_PROFILES.get(template, STYLE_PROFILES["report"])
    builder = SectionBuilder(profile)
    lines = md_text.split('\n')
    title = ""
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 빈 줄
        if not stripped:
            i += 1
            continue

        # YAML frontmatter 건너뛰기
        if stripped == '---' and i == 0:
            i += 1
            while i < len(lines) and lines[i].strip() != '---':
                i += 1
            i += 1  # closing ---
            continue

        # 수평선 (---)
        if re.match(r'^-{3,}$', stripped) or re.match(r'^\*{3,}$', stripped):
            builder.add_empty_line()
            i += 1
            continue

        # 제목 (# ~ ######)
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if heading_match:
            level = len(heading_match.group(1))
            heading_text = strip_markdown_formatting(heading_match.group(2))

            if level == 1:
                if not title:
                    title = heading_text
                builder.add_empty_line()
                builder.add_paragraph(heading_text, "title")
                builder.add_empty_line()
            elif level == 2:
                builder.add_empty_line()
                builder.add_paragraph(heading_text, "h2")
                builder.add_empty_line()
            else:  # 3-6
                builder.add_paragraph(heading_text, f"h{level}")
            i += 1
            continue

        # 인용 (>)
        if stripped.startswith('>'):
            quote_text = strip_markdown_formatting(stripped.lstrip('> '))
            builder.add_paragraph(quote_text, "quote")
            i += 1
            continue

        # 마크다운 테이블
        if '|' in stripped and i + 1 < len(lines) and re.match(r'^\|?\s*[-:]+', lines[i + 1].strip()):
            table_lines = [lines[i]]
            j = i + 1
            while j < len(lines) and '|' in lines[j] and lines[j].strip():
                table_lines.append(lines[j])
                j += 1
            headers, rows = parse_markdown_table(table_lines)
            if headers:
                builder.add_table(headers, rows)
            i = j
            continue

        # 목록 (- 또는 * 또는 숫자.)
        list_match = re.match(r'^(\s*)([-*]|\d+\.)\s+(.+)$', stripped)
        if list_match:
            indent = len(line) - len(line.lstrip())
            marker = list_match.group(2)
            content = strip_markdown_formatting(list_match.group(3))

            if indent >= 4:
                style = "list_l3"
                prefix = "    - "
            elif indent >= 2:
                style = "list_l2"
                prefix = "  - "
            else:
                style = "list_l1"
                if re.match(r'\d+\.', marker):
                    prefix = f"{marker} "
                else:
                    prefix = "- "

            builder.add_paragraph(f"{prefix}{content}", style)
            i += 1
            continue

        # 코드 블록 (``` 로 시작)
        if stripped.startswith('```'):
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            i += 1  # closing ```
            # 코드 블록을 일반 텍스트 문단으로 변환
            if code_lines:
                for cl in code_lines:
                    builder.add_paragraph(cl if cl.strip() else " ", "small")
            continue

        # 이미지 참조 (![alt](url)) - 텍스트로 변환
        img_match = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', stripped)
        if img_match:
            alt = img_match.group(1) or "이미지"
            builder.add_paragraph(f"[{alt}]", "small")
            i += 1
            continue

        # 일반 본문
        clean_text = strip_markdown_formatting(stripped)
        if '**' in stripped:
            # 볼드 혼합 텍스트
            runs = parse_inline_bold(stripped)
            # strip markdown from each run
            runs = [(sk, strip_markdown_formatting(t)) for sk, t in runs]
            if len(runs) > 1:
                builder.add_mixed_paragraph(runs, "body")
            else:
                builder.add_paragraph(clean_text, "body")
        else:
            builder.add_paragraph(clean_text, "body")

        i += 1

    return builder.build_xml(), title


# ─── 메인 ───────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="마크다운 파일을 HWPX 문서로 변환"
    )
    parser.add_argument("input", type=Path, help="입력 마크다운 파일")
    parser.add_argument("--output", "-o", type=Path, required=True, help="출력 HWPX 파일")
    parser.add_argument("--template", "-t", default="report",
                        choices=["base", "gonmun", "report", "minutes", "proposal"],
                        help="문서 템플릿 (기본: report)")
    parser.add_argument("--header", type=Path, help="커스텀 header.xml (선택)")
    parser.add_argument("--title", help="문서 제목 (자동 감지 가능)")
    parser.add_argument("--creator", help="작성자")
    parser.add_argument("--fix-ns", action="store_true", default=True,
                        help="네임스페이스 후처리 실행 (기본: 활성)")
    parser.add_argument("--no-fix-ns", action="store_true",
                        help="네임스페이스 후처리 건너뛰기")
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"ERROR: 입력 파일 없음: {args.input}", file=sys.stderr)
        sys.exit(1)

    # 1. 마크다운 읽기
    md_text = args.input.read_text(encoding="utf-8")
    print(f"입력: {args.input} ({len(md_text)} chars)")

    # 2. section0.xml 생성
    section_xml, auto_title = md_to_section(md_text, args.template)
    title = args.title or auto_title or args.input.stem

    # 3. 임시 section0.xml 저장
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as f:
        f.write(section_xml)
        section_path = Path(f.name)
    print(f"section0.xml 생성: {section_path}")

    # 4. build_hwpx.py 호출
    build_script = SCRIPT_DIR / "build_hwpx.py"
    cmd = [
        sys.executable, str(build_script),
        "--template", args.template,
        "--section", str(section_path),
        "--title", title,
        "--output", str(args.output),
    ]
    if args.creator:
        cmd.extend(["--creator", args.creator])
    if args.header:
        cmd.extend(["--header", str(args.header)])

    print(f"빌드: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"ERROR: build_hwpx.py 실패:\n{result.stderr}", file=sys.stderr)
        section_path.unlink(missing_ok=True)
        sys.exit(1)

    # 5. 네임스페이스 후처리
    if not args.no_fix_ns:
        fix_script = SCRIPT_DIR / "fix_namespaces.py"
        if fix_script.is_file():
            ns_result = subprocess.run(
                [sys.executable, str(fix_script), str(args.output)],
                capture_output=True, text=True
            )
            if ns_result.returncode == 0:
                print("네임스페이스 후처리 완료")
            else:
                print(f"WARNING: 네임스페이스 후처리 실패:\n{ns_result.stderr}", file=sys.stderr)
        else:
            print(f"WARNING: fix_namespaces.py 없음: {fix_script}", file=sys.stderr)

    # 6. 검증
    validate_script = SCRIPT_DIR / "validate.py"
    if validate_script.is_file():
        v_result = subprocess.run(
            [sys.executable, str(validate_script), str(args.output)],
            capture_output=True, text=True
        )
        print(v_result.stdout)

    # 7. 텍스트 추출 (요약)
    extract_script = SCRIPT_DIR / "text_extract.py"
    if extract_script.is_file():
        e_result = subprocess.run(
            [sys.executable, str(extract_script), str(args.output)],
            capture_output=True, text=True
        )
        extracted = e_result.stdout.strip()
        lines = extracted.split('\n')
        para_count = len([l for l in lines if l.strip()])
        print(f"문단 수: {para_count}")
        # 처음 5줄만 표시
        preview = '\n'.join(lines[:5])
        print(f"미리보기:\n{preview}\n...")

    # 정리
    section_path.unlink(missing_ok=True)
    print(f"\n완료: {args.output} ({args.output.stat().st_size / 1024:.1f}KB)")


if __name__ == "__main__":
    main()
