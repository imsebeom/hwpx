#!/usr/bin/env python3
"""add_equation.py — HWPX 본문·표 셀에 한컴 네이티브 수식 개체를 삽입한다.

이미지가 아니라 `<hp:equation>` 이므로 한글에서 수식 편집기로 그대로 열린다.
봉투 구조는 실물 문항지(수학)에서 뽑은 것을 따랐고, 스크립트 문법은
KS X 6101:2024 부속서 I 를 근거로 한다 (references/ks-x-6101.md).

수식은 자기완결 개체다. header.xml·BinData·매니페스트 등록이 필요 없고
`<hp:script>` 문자열만 있으면 된다.

CLI:
    # 본문: 앵커 문구가 있는 문단 뒤에 새 문단으로
    python add_equation.py in.hwpx -o out.hwpx --after "근의 공식" \
        --script "x = {-b +- sqrt{b^2 -4ac}} over {2a}"

    # 표 셀 안에 (좌표는 cellAddr 격자 기준 — 규칙 33과 동일)
    python add_equation.py in.hwpx -o out.hwpx --table 0 --row 1 --col 1 \
        --script "int _0 ^1 x^2 dx = 1 over 3"

API:
    from add_equation import add_equation
    add_equation("in.hwpx", "out.hwpx", script="a^2 + b^2 = c^2", after="피타고라스")
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import zipfile
from pathlib import Path

from lxml import etree

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from hwpx_helpers import ensure_dummy_linesegs_etree, xpath_local  # noqa: E402

HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"

# 실물 문항지에서 뽑은 기본값. baseUnit 은 수식 글자 크기(HWPUNIT/100)다.
DEFAULT_BASE_UNIT = 1000  # 10pt
EQ_FONT = "HYhwpEQ"  # 한컴 수식 전용 글꼴
EQ_VERSION = "Equation Version 60"


def _fresh_id(section_xml: str) -> int:
    """문서에서 쓰이지 않는 개체 id 를 고른다 (결정적)."""
    used = {int(v) for v in re.findall(r'\bid="(\d{4,})"', section_xml)}
    candidate = 2000000000
    while candidate in used:
        candidate += 1
    return candidate


def _estimate_size(script: str, base_unit: int) -> tuple[int, int]:
    """수식 개체의 표시 크기를 근사한다.

    한글은 문서를 열 때 수식을 다시 렌더링하므로 정확할 필요는 없으나,
    너무 작으면 첫 화면에서 잘려 보인다. 실물(baseUnit 1100, 2글자, 1050x1125)의
    글자당 폭 비율을 기준으로 잡았다.
    """
    lines = script.count("#") + 1
    # 중괄호·연산자 토큰은 렌더 폭에 거의 기여하지 않으므로 제외하고 센다
    visible = len(re.sub(r"[{}~`\s]", "", script))
    per_line = max(1, visible // lines)
    width = max(base_unit // 2, int(per_line * base_unit * 0.48))
    height = int(lines * base_unit * 1.02)
    return width, height


def build_equation_xml(
    script: str, eq_id: int, *, base_unit: int = DEFAULT_BASE_UNIT
) -> str:
    """인라인 `<hp:equation>` 봉투 한 개를 만든다.

    `treatAsChar="1"` 은 수식에서 옳다. 글자 크기의 인라인 개체라 쪽을 넘길 일이
    없기 때문이다 (쪽을 넘길 수 있는 표는 반대로 0이어야 한다 — 규칙 33).
    """
    width, height = _estimate_size(script, base_unit)
    body = escape_script(script)
    return (
        f'<hp:equation id="{eq_id}" zOrder="0" numberingType="EQUATION" '
        f'textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" '
        f'dropcapstyle="None" version="{EQ_VERSION}" baseLine="85" '
        f'textColor="#000000" baseUnit="{base_unit}" lineMode="CHAR" font="{EQ_FONT}">'
        f'<hp:sz width="{width}" widthRelTo="ABSOLUTE" height="{height}" '
        f'heightRelTo="ABSOLUTE" protect="0"/>'
        f'<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" '
        f'allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="PARA" '
        f'vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>'
        f'<hp:outMargin left="56" right="56" top="0" bottom="0"/>'
        f"<hp:shapeComment>수식입니다.</hp:shapeComment>"
        f"<hp:script>{body}</hp:script>"
        f"</hp:equation>"
    )


def escape_script(script: str) -> str:
    """수식 스크립트를 XML 텍스트로 안전하게 만든다.

    스크립트 문법의 `<`, `>`(부등호)와 `&`가 그대로 들어가면 XML 이 깨진다.
    """
    return script.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _make_equation_para(
    script: str, eq_id: int, *, para_pr: str, char_pr: str, base_unit: int
) -> etree._Element:
    """수식 하나만 담은 문단을 만든다."""
    eq = build_equation_xml(script, eq_id, base_unit=base_unit)
    xml = (
        f'<hp:p xmlns:hp="{HP}" id="0" paraPrIDRef="{para_pr}" styleIDRef="0" '
        f'pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="{char_pr}">{eq}</hp:run>'
        f"</hp:p>"
    )
    return etree.fromstring(xml.encode("utf-8"))


def _insert_after_anchor(
    root: etree._Element, anchor: str, script: str, eq_id: int, base_unit: int
) -> None:
    """앵커 문구가 있는 문단 바로 뒤에 수식 문단을 넣는다."""
    for para in xpath_local(root, "p"):
        text = "".join(t.text or "" for t in xpath_local(para, "t"))
        if anchor not in text:
            continue
        parent = para.getparent()
        run = para.find(f"{{{HP}}}run")
        new_para = _make_equation_para(
            script,
            eq_id,
            para_pr=para.get("paraPrIDRef", "0"),
            char_pr=run.get("charPrIDRef", "0") if run is not None else "0",
            base_unit=base_unit,
        )
        parent.insert(parent.index(para) + 1, new_para)
        return
    raise ValueError(f"앵커 문구를 찾지 못했다: {anchor!r}")


def _insert_in_cell(
    root: etree._Element,
    table_idx: int,
    row: int,
    col: int,
    script: str,
    eq_id: int,
    base_unit: int,
) -> None:
    """표 셀 안 문단 끝에 수식을 붙인다. 좌표는 cellAddr 격자 기준."""
    tables = xpath_local(root, "tbl")
    if table_idx >= len(tables):
        raise ValueError(f"표 {table_idx} 없음 (문서의 표 개수: {len(tables)})")

    for cell in xpath_local(tables[table_idx], "tc"):
        addr = cell.find(f"{{{HP}}}cellAddr")
        if addr is None:
            continue
        if int(addr.get("rowAddr", -1)) != row or int(addr.get("colAddr", -1)) != col:
            continue
        paras = xpath_local(cell, "p")
        if not paras:
            raise ValueError(f"셀 ({row},{col}) 에 문단이 없다")
        target = paras[-1]
        run = target.find(f"{{{HP}}}run")
        char_pr = run.get("charPrIDRef", "0") if run is not None else "0"
        eq_run = etree.fromstring(
            f'<hp:run xmlns:hp="{HP}" charPrIDRef="{char_pr}">'
            f"{build_equation_xml(script, eq_id, base_unit=base_unit)}"
            f"</hp:run>".encode("utf-8")
        )
        # 글이 바뀐 문단의 줄 배치 캐시는 지운다(SKILL.md 규칙 17). 그대로 두면 수식이 없던 때의 줄 높이가 남아 rhwp(에디터)가
        # 칸을 늘리지 않고 수식을 잘라 그렸다. run 은 linesegarray 앞에 와야 하므로 캐시를 먼저 떼고 붙인다(더미는 아래에서 다시 넣는다)
        for seg in target.findall(f"{{{HP}}}linesegarray"):
            target.remove(seg)
        target.append(eq_run)
        return
    raise ValueError(f"표 {table_idx} 에 셀 ({row},{col}) 이 없다")


def add_equation(
    src: str,
    dst: str,
    *,
    script: str,
    after: str | None = None,
    table: int | None = None,
    row: int | None = None,
    col: int | None = None,
    size_pt: float = 10.0,
    section: str = "Contents/section0.xml",
) -> None:
    """HWPX 에 수식 개체를 하나 삽입한다.

    Args:
        src: 원본 HWPX 경로
        dst: 출력 경로
        script: 한컴 수식 스크립트 (references/ks-x-6101.md 부속서 I)
        after: 이 문구가 든 문단 뒤에 새 문단으로 삽입
        table/row/col: 표 셀 안에 삽입 (cellAddr 격자 좌표)
        size_pt: 수식 글자 크기(pt)
    """
    if (after is None) == (table is None):
        raise ValueError("--after 또는 --table/--row/--col 중 하나만 지정한다")

    base_unit = int(round(size_pt * 100))

    with zipfile.ZipFile(src, "r") as zin:
        section_xml = zin.read(section).decode("utf-8")
        eq_id = _fresh_id(section_xml)
        root = etree.fromstring(section_xml.encode("utf-8"))

        if after is not None:
            _insert_after_anchor(root, after, script, eq_id, base_unit)
        else:
            if row is None or col is None:
                raise ValueError("--table 을 쓰면 --row 와 --col 도 필요하다")
            _insert_in_cell(root, table, row, col, script, eq_id, base_unit)

        ensure_dummy_linesegs_etree(root)
        new_xml = etree.tostring(root, encoding="UTF-8", xml_declaration=True)

        tmp = str(dst) + ".tmp"
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == section:
                    zout.writestr(item, new_xml)
                else:
                    # 원본 ZipInfo 를 넘겨 압축 방식을 보존한다.
                    # mimetype·version.xml 은 STORED 여야 한다 (KS X 6101 §8.3)
                    zout.writestr(item, zin.read(item.filename))

    os.replace(tmp, dst)


def main() -> None:
    p = argparse.ArgumentParser(
        description="HWPX 에 한컴 네이티브 수식 개체를 삽입한다"
    )
    p.add_argument("input", help="원본 HWPX")
    p.add_argument("--output", "-o", required=True, help="출력 HWPX")
    p.add_argument(
        "--script",
        "-s",
        required=True,
        help='수식 스크립트 (예: "x = {-b +- sqrt{b^2 -4ac}} over {2a}")',
    )
    p.add_argument("--after", help="이 문구가 든 문단 뒤에 새 문단으로 삽입")
    p.add_argument("--table", type=int, help="표 인덱스 (0부터)")
    p.add_argument("--row", type=int, help="행 좌표 (cellAddr rowAddr)")
    p.add_argument("--col", type=int, help="열 좌표 (cellAddr colAddr)")
    p.add_argument(
        "--size", type=float, default=10.0, help="수식 글자 크기 pt (기본 10)"
    )
    args = p.parse_args()

    add_equation(
        args.input,
        args.output,
        script=args.script,
        after=args.after,
        table=args.table,
        row=args.row,
        col=args.col,
        size_pt=args.size,
    )
    where = (
        f"'{args.after}' 뒤"
        if args.after
        else f"표 {args.table} ({args.row},{args.col})"
    )
    print(f"수식 삽입: {where} → {Path(args.output).name}")


if __name__ == "__main__":
    main()
