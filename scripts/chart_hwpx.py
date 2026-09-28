#!/usr/bin/env python3
"""HWPX 에 한글 네이티브 차트를 넣는다(그림이 아니라 한글에서 고칠 수 있는 차트).

kordoc(chrisryugj/kordoc, MIT) `src/hwpx/chart-gen.ts` 를 표준 라이브러리로 옮겼다. kordoc 은 차트 조립과
종류 표를 claw-hwp(DoHyun468, MIT)의 한컴독스 검증 구현에서 가져왔다.
HWPX 차트는 OLE 가 아니다. Chart/chartN.xml(OOXML DrawingML chartSpace)을 zip 에 넣고 content.hpf 에 등록한 뒤
본문에서 <hp:chart chartIDRef="Chart/chartN.xml"> 로 부른다. 차트는 글자처럼 취급해 넣은 자리에 앉는다.

데이터는 세 가지로 준다.
  JSON  {"type": "column", "cat": ["1분기", "2분기"], "series": {"예산": [10, 20], "집행": [5, 15]},
         "size": "120x70", "colors": ["#304D68", "accent2"]}
        series 는 [{"name": "예산", "values": [10, 20]}] 꼴도 된다.
  CSV   첫 행은 머리글(첫 칸은 항목 이름 머리, 나머지는 계열 이름), 다음 행부터 항목 이름과 값.
  펜스  kordoc ```chart 본문과 같은 "키: 값" 줄(type, cat, size, colors, point_colors, 그 밖은 "계열: 숫자들").

종류(--type): column(세로 막대), column_stacked, line(꺾은선), bar(가로 막대), bar_stacked, scatter(분산), pie(원),
  pie_explode, doughnut(도넛), area(영역), area_stacked, radar(방사형), bar3d, pie3d. 한글 이름(막대, 선, 원 등)도 받는다.

사용:
  python chart_hwpx.py 입력.hwpx 출력.hwpx --data 자료.json [--type line] [--anchor "문구"] [--before]
      [--size 120x70] [--colors "#304D68,accent2"]
  --anchor 를 주면 그 문구가 든 문단 뒤(--before 면 앞)에 차트 문단을 넣고, 없으면 첫 구역 끝에 넣는다.
"""

from __future__ import annotations

import argparse
import csv
import html
import io
import json
import math
import re
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from xml.sax.saxutils import escape

HU_PER_MM = 7200 / 25.4


@dataclass
class ChartSpec:
    el: str
    dir: str | None = None
    grp: str | None = None
    overlap: int | None = None
    marker: bool = False
    scatter: bool = False
    pie: bool = False
    explode: bool = False
    hole: int | None = None
    radar: bool = False


# 한컴독스 차트 20종(claw-hwp 검증)
CHART_TYPES = {
    0: ChartSpec("barChart", dir="col", grp="clustered"),
    1: ChartSpec("barChart", dir="col", grp="stacked", overlap=100),
    2: ChartSpec("lineChart", grp="standard", marker=True),
    3: ChartSpec("barChart", dir="bar", grp="clustered"),
    4: ChartSpec("barChart", dir="bar", grp="stacked", overlap=100),
    5: ChartSpec("scatterChart", scatter=True),
    6: ChartSpec("pieChart", pie=True),
    7: ChartSpec("pieChart", pie=True, explode=True),
    8: ChartSpec("doughnutChart", pie=True, hole=50),
    9: ChartSpec("areaChart", grp="standard"),
    10: ChartSpec("areaChart", grp="stacked"),
    11: ChartSpec("radarChart", radar=True),
    12: ChartSpec("bar3DChart", dir="col", grp="clustered"),
    13: ChartSpec("bar3DChart", dir="col", grp="stacked", overlap=100),
    14: ChartSpec("bar3DChart", dir="bar", grp="clustered"),
    15: ChartSpec("bar3DChart", dir="bar", grp="stacked", overlap=100),
    16: ChartSpec("pie3DChart", pie=True),
    17: ChartSpec("pie3DChart", pie=True, explode=True),
    18: ChartSpec("area3DChart", grp="standard"),
    19: ChartSpec("area3DChart", grp="stacked"),
}

CHART_ALIAS = {
    "column": 0, "col": 0, "세로막대": 0, "막대": 0,
    "column_stacked": 1, "세로막대_누적": 1,
    "line": 2, "선": 2, "꺾은선": 2,
    "bar": 3, "가로막대": 3,
    "bar_stacked": 4,
    "scatter": 5, "분산": 5,
    "pie": 6, "원": 6, "파이": 6,
    "pie_explode": 7,
    "doughnut": 8, "donut": 8, "도넛": 8,
    "area": 9, "영역": 9,
    "area_stacked": 10,
    "radar": 11, "방사형": 11,
    "bar3d": 12, "column3d": 12,
    "pie3d": 16,
}  # fmt: skip


def chart_spec(t: str | None) -> ChartSpec:
    if not t:
        return CHART_TYPES[0]
    key = CHART_ALIAS.get(t.strip().lower())
    if key is None and t.strip().isdigit():
        key = int(t)
    return CHART_TYPES.get(key, CHART_TYPES[0])


@dataclass
class Series:
    name: str
    values: list
    color: str | None = None
    point_colors: list | None = None


@dataclass
class Chart:
    spec: ChartSpec
    cat: list
    series: list = field(default_factory=list)
    width_hu: int = 32250
    height_hu: int = 18750


def _clamp_mm(n: float) -> float:
    # 크기 0 개체와 본문 폭을 넘는 차트를 막는다(10~500mm)
    return min(500.0, max(10.0, n))


def _parse_size(value) -> tuple[float, float] | None:
    m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*$", str(value), re.I)
    return (_clamp_mm(float(m.group(1))), _clamp_mm(float(m.group(2)))) if m else None


def _split(value: str) -> list[str]:
    return [s.strip() for s in value.split(",") if s.strip()]


def finish_chart(
    type_: str | None,
    cat,
    series: list[Series],
    size=None,
    colors=None,
    point_colors=None,
) -> Chart:
    """kordoc parseChartFence 의 뒷부분 — 원은 첫 계열만, 항목 수와 값 수를 맞춘다(모자란 값은 0)."""
    if not series:
        raise ValueError("계열(숫자 줄)이 하나도 없습니다")
    spec = chart_spec(type_)
    final = [
        Series(s.name, list(s.values)) for s in (series[:1] if spec.pie else series)
    ]
    # 계열이 항목보다 길면 값을 버리지 않고 「항목 N」으로 이름을 늘린다
    n = max([len(cat or [])] + [len(s.values) for s in final])
    cat_final = [
        (cat[i] if cat and i < len(cat) else f"항목 {i + 1}") for i in range(n)
    ]
    if not spec.scatter:
        for s in final:
            s.values = [s.values[i] if i < len(s.values) else 0 for i in range(n)]
    if spec.pie:
        slice_colors = colors or point_colors
        if slice_colors:
            final[0].point_colors = slice_colors
    else:
        if colors:
            for i, s in enumerate(final):
                s.color = colors[i % len(colors)]
        if point_colors and final:
            final[0].point_colors = point_colors
    w_mm, h_mm = size or (32250 / HU_PER_MM, 18750 / HU_PER_MM)
    return Chart(
        spec, cat_final, final, round(w_mm * HU_PER_MM), round(h_mm * HU_PER_MM)
    )


RESERVED = {"type", "cat", "size", "colors", "point_colors", "title"}


def parse_fence(text: str) -> Chart:
    """kordoc ```chart 본문 파싱. 숫자가 아닌 값이 섞인 계열 줄은 오류로 알린다(조용히 버리지 않는다)."""
    type_ = cat = size = colors = point_colors = None
    series: list[Series] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.search(r"[:：]", line)
        if not m or m.start() == 0:
            continue
        key, value = line[: m.start()].strip(), line[m.end() :].strip()
        k = key.lower()
        if k == "type":
            type_ = value
        elif k == "cat":
            cat = _split(value)
        elif k == "size":
            size = _parse_size(value) or size
        elif k == "colors":
            colors = _split(value)
        elif k == "point_colors":
            point_colors = _split(value)
        elif k not in RESERVED:
            # 천 단위 쉼표(1,000)를 한 숫자로 묶은 뒤 쉼표로 나눈다
            segs = _split(re.sub(r"(\d),(?=\d{3}(?:\D|$))", r"\1", value))
            if not segs:
                continue
            try:
                nums = [float(s) for s in segs]
            except ValueError:
                raise ValueError(
                    f"계열 「{key}」에 숫자가 아닌 값이 있습니다: {value}"
                ) from None
            if not all(math.isfinite(v) for v in nums):
                raise ValueError(f"계열 「{key}」에 유한하지 않은 값이 있습니다")
            series.append(Series(key, nums))
    return finish_chart(type_, cat, series, size, colors, point_colors)


def parse_json(obj: dict) -> Chart:
    raw = obj.get("series") or {}
    items = (
        raw.items()
        if isinstance(raw, dict)
        else ((s["name"], s["values"]) for s in raw)
    )
    series = [Series(str(name), [float(v) for v in values]) for name, values in items]
    size = obj.get("size")
    if isinstance(size, (list, tuple)) and len(size) == 2:
        size = (_clamp_mm(float(size[0])), _clamp_mm(float(size[1])))
    elif size is not None:
        size = _parse_size(size)
    colors = obj.get("colors")
    colors = _split(colors) if isinstance(colors, str) else colors
    pcs = obj.get("point_colors")
    pcs = _split(pcs) if isinstance(pcs, str) else pcs
    cat = [str(c) for c in obj.get("cat") or []] or None
    return finish_chart(obj.get("type"), cat, series, size, colors, pcs)


def parse_csv(text: str, type_=None, size=None, colors=None) -> Chart:
    rows = [r for r in csv.reader(io.StringIO(text)) if any(c.strip() for c in r)]
    if len(rows) < 2:
        raise ValueError("CSV 는 머리글 한 행과 자료 한 행 이상이 필요합니다")
    head, body = rows[0], rows[1:]
    cat = [r[0].strip() for r in body]
    series = []
    for j, name in enumerate(head[1:], start=1):
        vals = []
        for r in body:
            cell = r[j].strip().replace(",", "") if j < len(r) else ""
            try:
                vals.append(float(cell) if cell else 0.0)
            except ValueError:
                raise ValueError(
                    f"CSV {name} 열에 숫자가 아닌 값이 있습니다: {cell}"
                ) from None
        series.append(Series(name.strip(), vals))
    return finish_chart(type_, cat, series, size, colors)


# ---------------------------------------------------------------- chartSpace 조립


def _col_letter(i: int) -> str:
    return chr(66 + i)  # 0 → B


def _num(v) -> str:
    v = float(v) if v is not None else 0.0
    return str(int(v)) if v.is_integer() else repr(v)


def _str_cache(vals) -> str:
    return f'<c:ptCount val="{len(vals)}"/>' + "".join(
        f'<c:pt idx="{i}"><c:v>{escape(str(v))}</c:v></c:pt>'
        for i, v in enumerate(vals)
    )


def _num_cache(vals) -> str:
    return (
        f'<c:formatCode>General</c:formatCode><c:ptCount val="{len(vals)}"/>'
        + "".join(
            f'<c:pt idx="{i}"><c:v>{_num(v)}</c:v></c:pt>' for i, v in enumerate(vals)
        )
    )


def _color_fill(color: str | None) -> str | None:
    """accent1~6 은 한컴 내장 색, #RRGGBB 는 그 색. 그 밖은 무시."""
    if color is None:
        return None
    c = color.strip()
    if re.fullmatch(r"accent[1-6]", c, re.I):
        return f'<a:solidFill><a:schemeClr val="{c.lower()}"/></a:solidFill>'
    h = c.lstrip("#").upper()
    if re.fullmatch(r"[0-9A-F]{6}", h):
        return f'<a:solidFill><a:srgbClr val="{h}"/></a:solidFill>'
    return None


def _ser_sppr(color, stroke: bool) -> str:
    f = _color_fill(color)
    if not f:
        return "<c:spPr/>"
    if stroke:  # 선 모양(꺾은선, 방사형) 계열 색은 선 안에
        return (
            f'<c:spPr><a:ln w="28575" cap="flat" cmpd="sng" algn="ctr">{f}'
            f'<a:prstDash val="solid"/><a:round/></a:ln></c:spPr>'
        )
    return f"<c:spPr>{f}</c:spPr>"


def _dpt(point_colors, pie: bool) -> str:
    out = []
    for i, col in enumerate(point_colors or []):
        f = _color_fill(col)
        if not f:
            continue
        mid = (
            '<c:invertIfNegative val="0"/><c:bubble3D val="0"/><c:explosion val="0"/>'
            if pie
            else '<c:bubble3D val="0"/>'
        )
        out.append(f'<c:dPt><c:idx val="{i}"/>{mid}<c:spPr>{f}</c:spPr></c:dPt>')
    return "".join(out)


def _tx(idx: int, name: str) -> str:
    cl = _col_letter(idx)
    return (
        f'<c:tx><c:strRef><c:f>Sheet1!${cl}$1</c:f><c:strCache><c:ptCount val="1"/>'
        f'<c:pt idx="0"><c:v>{escape(name)}</c:v></c:pt></c:strCache></c:strRef></c:tx>'
    )


def _std_ser(idx, s: Series, cat, explode, stroke, pie) -> str:
    cl = _col_letter(idx)
    return (
        f'<c:ser><c:idx val="{idx}"/><c:order val="{idx}"/>{_tx(idx, s.name)}'
        f'{_ser_sppr(s.color, stroke)}<c:invertIfNegative val="0"/>'
        + ('<c:explosion val="25"/>' if explode else "")
        + _dpt(s.point_colors, pie)
        + f"<c:cat><c:strRef><c:f>Sheet1!$A$2:$A${len(cat) + 1}</c:f><c:strCache>{_str_cache(cat)}</c:strCache></c:strRef></c:cat>"
        + f"<c:val><c:numRef><c:f>Sheet1!${cl}$2:${cl}${len(s.values) + 1}</c:f><c:numCache>{_num_cache(s.values)}</c:numCache></c:numRef></c:val>"
        + "</c:ser>"
    )


def _scatter_ser(idx, s: Series, xs) -> str:
    cl = _col_letter(idx)
    return (
        f'<c:ser><c:idx val="{idx}"/><c:order val="{idx}"/>{_tx(idx, s.name)}'
        '<c:spPr><a:ln w="28575"><a:noFill/></a:ln></c:spPr><c:marker><c:symbol val="circle"/><c:size val="7"/></c:marker>'
        f"<c:xVal><c:numRef><c:f>Sheet1!$A$2:$A${len(xs) + 1}</c:f><c:numCache>{_num_cache(xs)}</c:numCache></c:numRef></c:xVal>"
        f"<c:yVal><c:numRef><c:f>Sheet1!${cl}$2:${cl}${len(s.values) + 1}</c:f><c:numCache>{_num_cache(s.values)}</c:numCache></c:numRef></c:yVal>"
        "</c:ser>"
    )


def _cat_ax(ax_id, pos, cross) -> str:
    return (
        f'<c:catAx><c:axId val="{ax_id}"/><c:scaling><c:orientation val="minMax"/></c:scaling><c:axPos val="{pos}"/>'
        f'<c:crossAx val="{cross}"/><c:delete val="0"/><c:majorTickMark val="out"/><c:minorTickMark val="none"/>'
        '<c:tickLblPos val="nextTo"/><c:crosses val="autoZero"/><c:auto val="1"/><c:lblAlgn val="ctr"/>'
        '<c:lblOffset val="100"/><c:noMultiLvlLbl val="0"/></c:catAx>'
    )


def _val_ax(ax_id, pos, cross) -> str:
    return (
        f'<c:valAx><c:axId val="{ax_id}"/><c:scaling><c:orientation val="minMax"/></c:scaling><c:axPos val="{pos}"/>'
        f'<c:majorGridlines/><c:numFmt formatCode="General" sourceLinked="1"/><c:crossAx val="{cross}"/>'
        '<c:delete val="0"/><c:majorTickMark val="out"/><c:minorTickMark val="none"/><c:tickLblPos val="nextTo"/>'
        '<c:crosses val="autoZero"/><c:crossBetween val="between"/></c:valAx>'
    )


def build_chart_space(ch: Chart) -> str:
    spec, cat, series = ch.spec, ch.cat, ch.series
    ns = (
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart"'
    )
    ax1, ax2 = "111111111", "222222222"
    if spec.scatter:
        # X 값: 항목 이름이 숫자면 그 값, 아니면 1부터 차례 번호
        n = max([0] + [len(s.values) for s in series])
        xs = []
        for i in range(n):
            try:
                v = float(cat[i]) if i < len(cat) and cat[i] != "" else None
            except ValueError:
                v = None
            xs.append(v if v is not None and math.isfinite(v) else i + 1)
        sers = "".join(_scatter_ser(i, s, xs) for i, s in enumerate(series))
        plot = (
            f'<c:scatterChart><c:scatterStyle val="lineMarker"/><c:varyColors val="0"/>{sers}'
            f'<c:axId val="{ax1}"/><c:axId val="{ax2}"/></c:scatterChart>'
            + _val_ax(ax1, "b", ax2)
            + _val_ax(ax2, "l", ax1)
        )
    elif spec.pie:
        s0 = series[0]
        plot = (
            f'<c:{spec.el}><c:varyColors val="1"/>{_std_ser(0, s0, cat, spec.explode, False, True)}'
            # pie3DChart 는 규격상 firstSliceAng 을 받지 않는다. 넣으면 한글이 조각을 그리지 않는다(원본 kordoc 과 다름)
            + ('<c:firstSliceAng val="0"/>' if spec.el != "pie3DChart" else "")
            + (f'<c:holeSize val="{spec.hole}"/>' if spec.hole is not None else "")
            + f"</c:{spec.el}>"
        )
    else:
        stroke = spec.el in ("lineChart", "radarChart") or spec.radar
        sers = "".join(
            _std_ser(i, s, cat, False, stroke, False) for i, s in enumerate(series)
        )
        horiz = spec.dir == "bar"
        inner = ""
        if spec.dir:
            inner += f'<c:barDir val="{spec.dir}"/>'
        if spec.grp:
            inner += f'<c:grouping val="{spec.grp}"/>'
        if spec.radar:
            inner += '<c:radarStyle val="standard"/>'
        inner += f'<c:varyColors val="0"/>{sers}'
        if spec.marker:
            inner += '<c:marker val="1"/>'
        if spec.el.startswith("bar"):
            inner += f'<c:gapWidth val="150"/><c:overlap val="{spec.overlap or 0}"/>'
        inner += f'<c:axId val="{ax1}"/><c:axId val="{ax2}"/>'
        plot = (
            f"<c:{spec.el}>{inner}</c:{spec.el}>"
            + _cat_ax(ax1, "l" if horiz else "b", ax2)
            + _val_ax(ax2, "b" if horiz else "l", ax1)
        )
    # 원 3D 는 보기 각도가 없으면 한글이 조각을 그리지 않는다(한글 PDF 실측, 원본 kordoc 에는 없음)
    view3d = (
        '<c:view3D><c:rotX val="30"/><c:rotY val="0"/><c:rAngAx val="0"/></c:view3D>'
        if spec.el == "pie3DChart"
        else ""
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'
        f'<c:chartSpace {ns}><c:date1904 val="0"/><c:roundedCorners val="0"/>'
        f'<c:chart><c:autoTitleDeleted val="0"/>{view3d}<c:plotArea><c:layout/>{plot}</c:plotArea>'
        '<c:legend><c:legendPos val="r"/><c:overlay val="0"/></c:legend>'
        '<c:plotVisOnly val="1"/><c:dispBlanksAs val="gap"/></c:chart></c:chartSpace>'
    )


def build_chart_element(part: str, w: int, h: int, cid: int) -> str:
    """본문 <hp:chart>. 글자처럼 취급(treatAsChar=1)이라 넣은 자리에 앉고 다른 쪽으로 떠내려가지 않는다."""
    return (
        f'<hp:chart id="{cid}" zOrder="0" numberingType="PICTURE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" '
        f'lock="0" dropcapstyle="None" chartIDRef="{part}">'
        f'<hp:sz width="{w}" widthRelTo="ABSOLUTE" height="{h}" heightRelTo="ABSOLUTE" protect="0"/>'
        '<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" '
        'vertRelTo="PARA" horzRelTo="PARA" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>'
        '<hp:outMargin left="709" right="709" top="709" bottom="709"/></hp:chart>'
    )


# ---------------------------------------------------------------- 문서에 넣기


def _section_key(name: str) -> int:
    m = re.search(r"(\d+)\.xml$", name)
    return int(m.group(1)) if m else 0


def _para_spans(xml: str):
    """최상위(구역 바로 아래) 문단의 (시작, 끝) 목록. 표 안 문단은 바깥 문단에 포함된다."""
    spans, depth, start = [], 0, 0
    for m in re.finditer(r"<(/?)hp:p\b[^>]*?(/?)>", xml):
        closing, selfclose = m.group(1), m.group(2)
        if closing:
            depth -= 1
            if depth == 0:
                spans.append((start, m.end()))
        elif not selfclose:
            if depth == 0:
                start = m.start()
            depth += 1
    return spans


def _plain(xml_fragment: str) -> str:
    return "".join(
        re.sub(r"<[^>]+>", "", t)
        for t in re.findall(r"<hp:t\b[^>]*>(.*?)</hp:t>", xml_fragment, re.S)
    )


def insert_chart(
    src: str, dst: str, ch: Chart, anchor: str | None = None, before: bool = False
) -> dict:
    with zipfile.ZipFile(src) as zi:
        names = zi.namelist()
        secs = sorted(
            (n for n in names if re.search(r"Contents/section\d+\.xml$", n)),
            key=_section_key,
        )
        if not secs:
            raise ValueError("섹션 파일이 없습니다")
        hpf_name = next((n for n in names if n.lower().endswith(".hpf")), None)
        if not hpf_name:
            raise ValueError("content.hpf 가 없습니다")
        hpf = zi.read(hpf_name).decode("utf-8")
        texts = {n: zi.read(n).decode("utf-8") for n in secs}

        # 넣을 자리
        target, pos, host = secs[0], None, None
        if anchor:
            for n in secs:
                for a, b in _para_spans(texts[n]):
                    if anchor in html.unescape(_plain(texts[n][a:b])):
                        target, pos, host = n, (a if before else b), texts[n][a:b]
                        break
                if pos is not None:
                    break
            if pos is None:
                raise ValueError(f'문구 "{anchor}" 가 든 문단을 찾지 못했습니다')
        else:
            spans = _para_spans(texts[target])
            if not spans:
                raise ValueError("문단이 없습니다")
            host = texts[target][spans[-1][0] : spans[-1][1]]
            pos = spans[-1][1]

        # 번호: 기존 Chart/chartN 과 매니페스트 id, 개체 id 와 겹치지 않게
        used_items = set(re.findall(r'<opf:item\b[^>]*\bid="([^"]+)"', hpf))
        n = 1
        while (
            f"Contents/Chart/chart{n}.xml" in names
            or f"Chart/chart{n}.xml" in names
            or f"chart{n}" in used_items
        ):
            n += 1
        part = f"Chart/chart{n}.xml"
        max_id = 9_100_000
        for x in texts.values():
            for v in re.findall(r'\b(?:id|instid)="(\d+)"', x):
                max_id = max(max_id, int(v))

        para_pr = re.search(r'paraPrIDRef="(\d+)"', host or "")
        char_pr = re.search(r'charPrIDRef="(\d+)"', host or "")
        para = (
            f'<hp:p id="0" paraPrIDRef="{para_pr.group(1) if para_pr else 0}" styleIDRef="0" pageBreak="0" '
            f'columnBreak="0" merged="0"><hp:run charPrIDRef="{char_pr.group(1) if char_pr else 0}">'
            f"{build_chart_element(part, ch.width_hu, ch.height_hu, max_id + 1)}</hp:run></hp:p>"
        )
        texts[target] = texts[target][:pos] + para + texts[target][pos:]
        item = f'<opf:item id="chart{n}" href="{part}" media-type="application/xml"/>'
        if "</opf:manifest>" not in hpf:
            raise ValueError("content.hpf 에 manifest 가 없습니다")
        hpf = hpf.replace("</opf:manifest>", item + "</opf:manifest>")

        tmp = dst + ".tmp"
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zo:
            for info in zi.infolist():
                if info.filename == target:
                    data = texts[target].encode("utf-8")
                elif info.filename == hpf_name:
                    data = hpf.encode("utf-8")
                else:
                    data = zi.read(info.filename)
                ct = (
                    zipfile.ZIP_STORED
                    if info.filename == "mimetype"
                    else zipfile.ZIP_DEFLATED
                )
                zo.writestr(info, data, compress_type=ct)
            zo.writestr(part, build_chart_space(ch).encode("utf-8"))
    Path(tmp).replace(dst)
    return {
        "part": part,
        "section": target,
        "type": ch.spec.el,
        "series": [s.name for s in ch.series],
        "categories": len(ch.cat),
        "size_mm": [
            round(ch.width_hu / HU_PER_MM, 1),
            round(ch.height_hu / HU_PER_MM, 1),
        ],
    }


def load_chart(path: str, type_=None, size=None, colors=None) -> Chart:
    text = Path(path).read_text(encoding="utf-8-sig")
    suffix = Path(path).suffix.lower()
    size_t = _parse_size(size) if size else None
    color_l = _split(colors) if colors else None
    if suffix == ".json":
        obj = json.loads(text)
        if type_:
            obj["type"] = type_
        if size_t:
            obj["size"] = list(size_t)
        if color_l:
            obj["colors"] = color_l
        return parse_json(obj)
    if suffix == ".csv":
        return parse_csv(text, type_, size_t, color_l)
    ch = parse_fence(text)
    if type_ or size_t or color_l:
        # 명령줄 값이 펜스보다 앞선다
        extra = [f"type: {type_}"] if type_ else []
        extra += [f"size: {size}"] if size_t else []
        extra += [f"colors: {colors}"] if color_l else []
        ch = parse_fence(text + "\n" + "\n".join(extra))
    return ch


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="HWPX 에 한글 네이티브 차트 넣기")
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument(
        "--data", required=True, help="자료 파일(.json, .csv, 그 밖은 kordoc 펜스 글)"
    )
    ap.add_argument(
        "--type",
        default=None,
        help="차트 종류(column, line, bar, pie, doughnut, area, radar, scatter …)",
    )
    ap.add_argument(
        "--anchor",
        default=None,
        help="이 문구가 든 문단 뒤에 넣는다(없으면 첫 구역 끝)",
    )
    ap.add_argument("--before", action="store_true", help="문구가 든 문단 앞에 넣는다")
    ap.add_argument("--size", default=None, help="너비x높이 mm(기본 113.8x66.1)")
    ap.add_argument(
        "--colors", default=None, help='계열 색(원은 조각 색). "#304D68,accent2" 꼴'
    )
    a = ap.parse_args()
    try:
        ch = load_chart(a.data, a.type, a.size, a.colors)
        info = insert_chart(a.input, a.output, ch, a.anchor, a.before)
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        print(f"오류: {e}", file=sys.stderr)
        return 1
    print(json.dumps(info, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
