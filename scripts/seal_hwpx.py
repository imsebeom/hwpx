#!/usr/bin/env python3
"""HWPX 도장 날인 — 「(인)」, 「서명 또는 인」 같은 문구 위에 도장 그림을 글 앞으로 띄워 넣는다.

kordoc(chrisryugj/kordoc, MIT) `src/form/seal.ts` 를 표준 라이브러리로 옮겼다.
원리는 원본과 같다.
- 문구가 든 문단에 글 앞(IN_FRONT_OF_TEXT) 그림을 단다. treatAsChar="0", flowWithText="0",
  allowOverlap="1" 이라 칸이나 쪽이 그림 높이만큼 늘지 않는다(flowWithText="1" 이면 한글이 칸을 키운다).
- 가로 위치는 글자 폭으로 어림한다. 한글과 전각은 1em, ASCII 와 반각은 0.5em, 고정폭 빈칸은 0.25em,
  em 은 런마다 제 글자 크기이고 장평과 자간을 반영한다. 가운데, 오른쪽 정렬 문단은 남는 폭만큼 민다.
- 한글은 칸 안 글 앞 그림의 가로 위치를 단 원점에서 잰다. 그래서 같은 행 앞 칸들의 폭을 더한다
  (표 속 표는 바깥 칸 몫까지).
- 세로는 저장된 줄 배치(linesegarray)로 문구가 든 줄 가운데에 앉힌다. 한글은 칸 문단의 글 앞 그림을
  칸이 아니라 표 위에서 재므로 앞 행 높이와 칸 위 여백을 더한다(원본 kordoc 에는 없는 보정, 한글 PDF 실측).
  줄 배치가 없으면 원본처럼 문단 첫 줄 기준으로 어림한다.
- 표가 쪽을 넘으면 뒤 쪽 문구의 도장은 한글이 앞 쪽에 걸거나 그리지 않는다. 이때는 경고를 낸다.
- 기본은 문구 위에 겹쳐 찍는다(overlap). 원본 기본값(auto, 자리가 있으면 오른쪽)은 --mode auto.

머리말, 꼬리말, 각주, 미주 안의 문구는 찾지 않는다. 바꾸지 않는 zip 항목은 그대로 옮긴다.

사용:
  python seal_hwpx.py 입력.hwpx 출력.hwpx --image 도장.png [--anchor "(인)"]
      [--occurrence 0 | --occurrence 0,2 | --occurrence all] [--size 12] [--mode overlap|right|auto]
      [--dx 0] [--dy 0]
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

HU_PER_MM = 7200 / 25.4

MIME = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "bmp": "image/bmp",
    "gif": "image/gif",
}

# 이 요소 안의 문단은 찾지 않는다
EXCLUDED = {"header", "footer", "footNote", "endNote", "masterPage"}


def image_magic_matches(data: bytes, ext: str) -> bool:
    if ext == "png":
        return data[:4] == b"\x89PNG"
    if ext in ("jpg", "jpeg"):
        return data[:3] == b"\xff\xd8\xff"
    if ext == "bmp":
        return data[:2] == b"BM"
    if ext == "gif":
        return data[:3] == b"GIF"
    return False


def glyph_em(ch: str) -> float:
    code = ord(ch)
    if code < 0x20:
        return 0.0
    if code <= 0x7E:
        return 0.5
    if 0xFF61 <= code <= 0xFFDC:
        return 0.5
    if code == 0x2005:
        return 0.25
    return 1.0


def measure_mm(text: str, em_mm: float, style: dict | None = None) -> float:
    """글자 폭 합(mm). style 이 있으면 장평(ratio)과 자간(spacing, em 의 %)을 반영한다.
    한글은 글자 폭을 (글꼴 폭 x 장평 + 자간) x 글자 크기로 잡는다."""
    style = style or {}
    w = 0.0
    for c in text:
        g = glyph_em(c)
        if g == 0:
            continue
        side = "latin" if ord(c) <= 0x7E else "hangul"
        w += (
            g * style.get(f"ratio_{side}", 100) / 100
            + style.get(f"spacing_{side}", 0) / 100
        )
    return w * em_mm


# ---------------------------------------------------------------- 섹션 훑기


@dataclass
class Cell:
    attrs: dict = field(
        default_factory=dict
    )  # colAddr, colSpan, width, marginL, marginR
    table: "Table | None" = None


@dataclass
class Table:
    cells: list = field(default_factory=list)


@dataclass
class Run:
    char_pr: str
    prefix: str
    text: str = ""
    close_end: int = -1


@dataclass
class Para:
    start: int
    open_tag: str
    text: str = ""
    runs: list = field(default_factory=list)
    cell: Cell | None = None
    outer: list = field(
        default_factory=list
    )  # 바깥 칸들(가까운 순서가 아니라 바깥부터)
    in_textbox: bool = False
    host: "Para | None" = None  # 표를 담은 본문 문단(칸 문단일 때)
    has_tab: bool = False
    has_break: bool = False
    lines: list = field(
        default_factory=list
    )  # 저장된 줄 배치(textpos, vertpos, vertsize, horzpos)


# t 안의 빈 요소 글자. 고정폭 빈칸(fwSpace)은 한글 PDF 실측 0.25em 이라 U+2005(4분 빈칸)로 둔다.
# 묶음 빈칸(nbSpace)은 보통 빈칸과 같다
SPECIAL_CHARS = {
    "fwSpace": " ",
    "nbSpace": " ",
    "hyphen": "-",
    "tab": "\t",
    "lineBreak": "\n",
    "br": "\n",
}


TAG_RE = re.compile(r"<(/?)([A-Za-z0-9]+):([A-Za-z0-9]+)\b([^>]*?)(/?)>")


def _attr(tag_attrs: str, name: str) -> str | None:
    m = re.search(r"\b" + name + r'="([^"]*)"', tag_attrs)
    return m.group(1) if m else None


def scan_section(xml: str) -> list[Para]:
    """문단을 문서 순서로 모은다. 칸 문단은 소속 칸과 바깥 칸을 기억한다."""
    paras: list[Para] = []
    stack: list[tuple[str, object]] = []  # (local, 객체)
    last = 0
    for m in TAG_RE.finditer(xml):
        # 태그 사이 글: 가장 안쪽이 t 이면 문단 글
        if m.start() > last and stack and stack[-1][0] == "t":
            chunk = html.unescape(xml[last : m.start()])
            para = _innermost(stack, "p")
            run = _innermost(stack, "run")
            if para is not None:
                para.text += chunk
            if run is not None:
                run.text += chunk
        last = m.end()
        closing, prefix, local, attrs, selfclose = m.groups()
        if closing:
            # 짝 맞는 여는 태그까지 걷는다
            while stack:
                top_local, obj = stack.pop()
                if top_local == local:
                    if local == "run" and isinstance(obj, Run):
                        obj.close_end = m.end()
                    break
            continue
        if local == "p":
            if any(s[0] in EXCLUDED for s in stack):
                para = None
            else:
                cells = [o for (name, o) in stack if name == "tc"]
                para = Para(
                    start=m.start(),
                    open_tag=m.group(0),
                    cell=cells[-1] if cells else None,
                    outer=cells[:-1],
                    in_textbox=any(s[0] == "drawText" for s in stack),
                    host=next((o for (name, o) in stack if name == "p"), None),
                )
                paras.append(para)
            if not selfclose:
                stack.append(("p", para))
            continue
        if local == "run":
            para = _innermost(stack, "p")
            run = Run(char_pr=_attr(attrs, "charPrIDRef") or "0", prefix=prefix)
            if para is not None:
                para.runs.append(run)
            if not selfclose:
                stack.append(("run", run))
            continue
        if local == "tbl":
            if not selfclose:
                stack.append(("tbl", Table()))
            continue
        if local == "tc":
            table = _innermost(stack, "tbl")
            cell = Cell(table=table)
            if table is not None:
                table.cells.append(cell)
            if not selfclose:
                stack.append(("tc", cell))
            continue
        cell = (
            _innermost(stack, "tc")
            if local in ("cellAddr", "cellSpan", "cellSz", "cellMargin")
            else None
        )
        # 칸 속성은 그 칸의 직계일 때만(표 속 표의 칸 속성이 바깥 칸에 붙지 않게)
        if cell is not None and stack and stack[-1][0] == "tc":
            if local == "cellAddr":
                cell.attrs["colAddr"] = int(_attr(attrs, "colAddr") or 0)
                cell.attrs["rowAddr"] = int(_attr(attrs, "rowAddr") or 0)
            elif local == "cellSpan":
                cell.attrs["colSpan"] = int(_attr(attrs, "colSpan") or 1)
                cell.attrs["rowSpan"] = int(_attr(attrs, "rowSpan") or 1)
            elif local == "cellSz":
                cell.attrs["width"] = int(_attr(attrs, "width") or 0)
                cell.attrs["height"] = int(_attr(attrs, "height") or 0)
            elif local == "cellMargin":
                cell.attrs["marginL"] = int(_attr(attrs, "left") or 0)
                cell.attrs["marginR"] = int(_attr(attrs, "right") or 0)
                cell.attrs["marginT"] = int(_attr(attrs, "top") or 0)
        if local in SPECIAL_CHARS:
            para = _innermost(stack, "p")
            run = _innermost(stack, "run")
            ch = SPECIAL_CHARS[local]
            if para is not None:
                para.text += ch
                para.has_tab |= local == "tab"
                para.has_break |= local in ("lineBreak", "br")
            if run is not None:
                run.text += ch
        if local == "lineseg":
            para = _innermost(stack, "p")
            if para is not None:
                para.lines.append(
                    {
                        k: int(_attr(attrs, k) or 0)
                        for k in (
                            "textpos",
                            "vertpos",
                            "vertsize",
                            "horzpos",
                            "horzsize",
                        )
                    }
                )
        if not selfclose:
            stack.append((local, None))
    return paras


def _innermost(stack, local):
    for name, o in reversed(stack):
        if name == local:
            return o
        # 문단을 찾을 때 칸 경계를 넘지 않는다
        if local == "p" and name == "tc":
            return None
        if local == "run" and name == "p":
            return None
    return None


# ---------------------------------------------------------------- 스타일, 폭


def parse_styles(header_xml: str) -> tuple[dict, dict]:
    char_h: dict[str, dict] = {}
    for m in re.finditer(
        r"<[A-Za-z0-9]+:charPr\b([^>]*)>(.*?)</[A-Za-z0-9]+:charPr>", header_xml, re.S
    ):
        cid, h = _attr(m.group(1), "id"), _attr(m.group(1), "height")
        if cid is None or not h:
            continue
        st = {"height": int(h)}
        for tag, key in (("ratio", "ratio"), ("spacing", "spacing")):
            t = re.search(r"<[A-Za-z0-9]+:" + tag + r"\b([^>]*)>", m.group(2))
            if t:
                st[f"{key}_hangul"] = int(
                    _attr(t.group(1), "hangul") or (100 if key == "ratio" else 0)
                )
                st[f"{key}_latin"] = int(
                    _attr(t.group(1), "latin") or (100 if key == "ratio" else 0)
                )
        char_h[cid] = st
    para_align: dict[str, str] = {}
    for m in re.finditer(
        r"<[A-Za-z0-9]+:paraPr\b([^>]*)>(.*?)</[A-Za-z0-9]+:paraPr>", header_xml, re.S
    ):
        pid = _attr(m.group(1), "id")
        a = re.search(r'<[A-Za-z0-9]+:align\b[^>]*\bhorizontal="([A-Z]+)"', m.group(2))
        if pid is not None and a:
            para_align[pid] = a.group(1)
    return char_h, para_align


def cell_content_mm(cell: Cell) -> float | None:
    w = cell.attrs.get("width")
    if not w:
        return None
    w -= cell.attrs.get("marginL", 0) + cell.attrs.get("marginR", 0)
    return w / HU_PER_MM if w > 0 else None


def cell_left_mm(cell: Cell) -> float:
    """같은 표에서 앞 열들의 폭 합. 병합 칸(colSpan>1)은 열 폭 확정에 쓰지 않는다."""
    col = cell.attrs.get("colAddr")
    if not col or cell.table is None:
        return 0.0
    col_w: dict[int, int] = {}
    for c in cell.table.cells:
        a = c.attrs.get("colAddr")
        if a is None or a in col_w or c.attrs.get("colSpan", 1) > 1:
            continue
        if c.attrs.get("width"):
            col_w[a] = c.attrs["width"]
    return sum(col_w.get(i, 0) for i in range(col)) / HU_PER_MM


def cell_top_mm(cell: Cell) -> float:
    """표 위에서 칸 글 영역 위까지(앞 행 높이 합 + 칸 위 여백).

    한글은 칸 문단에 단 글 앞 그림(flowWithText=0)의 세로 위치를 칸이 아니라 표 위에서 잰다(한글 PDF 실측).
    행 높이는 병합하지 않은 칸의 cellSz 높이로 정한다."""
    row = cell.attrs.get("rowAddr", 0)
    row_h: dict[int, int] = {}
    if cell.table is not None:
        for c in cell.table.cells:
            r = c.attrs.get("rowAddr")
            if r is None or c.attrs.get("rowSpan", 1) > 1:
                continue
            row_h[r] = max(row_h.get(r, 0), c.attrs.get("height", 0))
    return (
        sum(row_h.get(i, 0) for i in range(row)) + cell.attrs.get("marginT", 0)
    ) / HU_PER_MM


def body_column_mm(xml: str) -> float:
    page = re.search(r'<[A-Za-z0-9]+:pagePr\b[^>]*\bwidth="(\d+)"', xml)
    margin = re.search(
        r'<[A-Za-z0-9]+:margin\b[^>]*\bleft="(\d+)"[^>]*\bright="(\d+)"', xml
    )
    if not page:
        return 150.0
    w = int(page.group(1)) - (
        int(margin.group(1)) + int(margin.group(2)) if margin else 0
    )
    return w / HU_PER_MM if w > 0 else 150.0


def body_height_mm(xml: str) -> float:
    """본문 높이(mm) — 용지 높이에서 위, 아래, 머리말, 꼬리말 여백을 뺀 값."""
    page = re.search(r'<[A-Za-z0-9]+:pagePr\b[^>]*\bheight="(\d+)"', xml)
    margin = re.search(r"<[A-Za-z0-9]+:margin\b([^>]*)>", xml)
    if not page:
        return 250.0
    h = int(page.group(1))
    if margin:
        h -= sum(
            int(_attr(margin.group(1), k) or 0)
            for k in ("top", "bottom", "header", "footer")
        )
    return h / HU_PER_MM


def build_float_pic(
    item_id: str, size_hu: int, x_hu: int, y_hu: int, pid: int, instid: int
) -> str:
    w = h = size_hu
    return (
        f'<hp:pic xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core" id="{pid}" zOrder="0" '
        f'numberingType="PICTURE" textWrap="IN_FRONT_OF_TEXT" textFlow="BOTH_SIDES" lock="0" '
        f'dropcapstyle="None" href="" groupLevel="0" instid="{instid}" reverse="0">'
        f'<hp:offset x="0" y="0"/><hp:orgSz width="{w}" height="{h}"/><hp:curSz width="{w}" height="{h}"/>'
        f'<hp:flip horizontal="0" vertical="0"/>'
        f'<hp:rotationInfo angle="0" centerX="{w // 2}" centerY="{h // 2}" rotateimage="1"/>'
        f'<hp:renderingInfo><hc:transMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/>'
        f'<hc:scaMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/>'
        f'<hc:rotMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/></hp:renderingInfo>'
        f'<hp:imgRect><hc:pt0 x="0" y="0"/><hc:pt1 x="{w}" y="0"/><hc:pt2 x="{w}" y="{h}"/>'
        f'<hc:pt3 x="0" y="{h}"/></hp:imgRect>'
        f'<hp:imgClip left="0" right="{w}" top="0" bottom="{h}"/>'
        f'<hp:inMargin left="0" right="0" top="0" bottom="0"/>'
        f'<hp:imgDim dimwidth="{w}" dimheight="{h}"/>'
        f'<hc:img binaryItemIDRef="{item_id}" bright="0" contrast="0" effect="REAL_PIC" alpha="0"/>'
        f"<hp:effects/>"
        f'<hp:sz width="{w}" widthRelTo="ABSOLUTE" height="{h}" heightRelTo="ABSOLUTE" protect="0"/>'
        # 가로 COLUMN: 칸 안에서는 PARA 로 두면 한글이 표를 담은 바깥 문단을 원점으로 잡아 옆 칸으로 밀린다
        f'<hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="0" allowOverlap="1" '
        f'holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" '
        f'vertOffset="{y_hu}" horzOffset="{x_hu}"/>'
        f'<hp:outMargin left="0" right="0" top="0" bottom="0"/><hp:shapeComment>seal</hp:shapeComment>'
        f"</hp:pic>"
    )


# ---------------------------------------------------------------- 날인


def section_sort_key(name: str) -> int:
    m = re.search(r"(\d+)\.xml$", name, re.I)
    return int(m.group(1)) if m else 0


def measure_para_mm(p: Para, a: int, b: int, styles: dict) -> float:
    """문단 글 [a, b) 의 폭(mm). 런마다 제 글자 모양으로 잰다."""
    w, pos = 0.0, 0
    for r in p.runs:
        lo, hi = max(a, pos), min(b, pos + len(r.text))
        if lo < hi:
            st = styles.get(r.char_pr, {})
            w += measure_mm(
                r.text[lo - pos : hi - pos],
                st.get("height", 1000) / 100 * 25.4 / 72,
                st,
            )
        pos += len(r.text)
    return w


def _is_dummy(ln: dict) -> bool:
    return ln["vertpos"] == 0 and ln["vertsize"] == 900 and ln["horzsize"] == 22960


def find_anchor_run(para: Para, anchor: str) -> Run | None:
    runs = [r for r in para.runs if r.close_end > 0]
    for r in runs:
        if anchor in r.text:
            return r
    for r in runs:
        if anchor[0] in r.text:
            return r
    return runs[-1] if runs else None


def place_seals(
    src: str,
    dst: str,
    image: bytes,
    ext: str,
    anchor: str,
    occurrences,
    size_mm=None,
    mode="overlap",
    dx=0.0,
    dy=0.0,
) -> list[dict]:
    ext = ext.lower()
    if ext not in MIME:
        raise ValueError(f"지원하지 않는 그림 확장자 .{ext} (png, jpg, bmp, gif)")
    if not image_magic_matches(image, ext):
        raise ValueError(f"그림 내용이 .{ext} 형식이 아닙니다")

    with zipfile.ZipFile(src) as zi:
        names = zi.namelist()
        sec_names = sorted(
            [n for n in names if re.search(r"section\d+\.xml$", n, re.I)],
            key=section_sort_key,
        )
        if not sec_names:
            raise ValueError("섹션 파일이 없습니다")
        hpf_name = next((n for n in names if n.lower().endswith(".hpf")), None)
        header_name = next(
            (n for n in names if re.search(r"(^|/)header\.xml$", n, re.I)), None
        )
        secs = [zi.read(n).decode("utf-8") for n in sec_names]
        hpf = zi.read(hpf_name).decode("utf-8") if hpf_name else ""
        char_h, para_align = (
            parse_styles(zi.read(header_name).decode("utf-8"))
            if header_name
            else ({}, {})
        )

        # 모든 등장 위치
        hits = []
        scans = [scan_section(x) for x in secs]
        for si, paras in enumerate(scans):
            for p in paras:
                i = p.text.find(anchor)
                while i != -1:
                    hits.append((si, p, i))
                    i = p.text.find(anchor, i + len(anchor))
        if occurrences == "all":
            chosen = list(range(len(hits)))
        else:
            chosen = list(occurrences)
        bad = [o for o in chosen if o < 0 or o >= len(hits)]
        if not hits or bad:
            raise ValueError(
                f'문구 "{anchor}" 의 {bad or chosen} 번째 등장을 찾지 못했습니다 '
                f"(본문 {len(hits)}회 등장, 0..{max(0, len(hits) - 1)})"
            )

        used_ids = set(re.findall(r'<opf:item\b[^>]*\bid="([^"]+)"', hpf))
        used_nums = {
            int(m.group(1))
            for n in names
            if (m := re.match(r"BinData/(?:image|img)(\d+)\.", n, re.I))
        }
        max_id = 1_000_000
        for x in secs:
            for v in re.findall(r'\b(?:id|instid)="(\d+)"', x):
                max_id = max(max_id, int(v))

        splices: list[list[tuple[int, str]]] = [[] for _ in secs]
        additions: dict[str, bytes] = {}
        items = []
        placed = []
        for occ in chosen:
            si, p, idx = hits[occ]
            xml = secs[si]
            run = find_anchor_run(p, anchor)
            if run is None:
                raise ValueError(f'문구 "{anchor}" 문단에서 런을 찾지 못했습니다')
            style = char_h.get(run.char_pr, {})
            em_mm = style.get("height", 1000) / 100 * 25.4 / 72
            # 저장된 줄 배치가 있으면 문구가 든 줄의 자리(세로, 줄 시작)를 쓴다
            # 스킬 생성본의 더미 줄 배치(hwpx_helpers.LINESEG_DUMMY: 모든 문단 vertpos 0)는 자리 정보가 아니다
            lines = [ln for ln in p.lines if ln["vertsize"] > 0 and not _is_dummy(ln)]
            line = None
            if lines:
                line = [ln for ln in lines if ln["textpos"] <= idx][-1:] or lines[:1]
                line = line[0]
            line_start = line["textpos"] if line else 0
            line_end = next(
                (ln["textpos"] for ln in lines if ln["textpos"] > line_start),
                len(p.text),
            )
            horz = line["horzpos"] / HU_PER_MM if line else 0.0
            start_x = horz + measure_para_mm(p, line_start, idx, char_h)
            anchor_w = measure_mm(anchor, em_mm, style)
            size = (
                size_mm if size_mm and size_mm > 0 else max(7.0, min(18.0, em_mm * 1.6))
            )

            avail = (cell_content_mm(p.cell) if p.cell else None) or body_column_mm(xml)
            align = para_align.get(_attr(p.open_tag, "paraPrIDRef") or "0")
            shift = 0.0
            if align in ("CENTER", "RIGHT"):
                pw = measure_para_mm(p, line_start, line_end, char_h)
                room = avail - horz - pw
                shift = room / 2 if align == "CENTER" else room
                shift = max(0.0, shift)
            m = mode
            if m == "auto":
                m = (
                    "right"
                    if avail - (shift + start_x + anchor_w) >= size + 2
                    else "overlap"
                )
            cell_shift = 0.0
            if p.cell is not None:
                cell_shift = cell_left_mm(p.cell) + sum(
                    cell_left_mm(c) for c in p.outer
                )
            base = (
                start_x + anchor_w + 2
                if m == "right"
                else start_x + anchor_w / 2 - size / 2
            )
            pos_x = base + shift + cell_shift + dx
            if line:
                # 칸 문단은 표 위가 기준(cell_top_mm + 칸 줄 배치), 본문 문단은 그 문단이 기준이다
                top = line["vertpos"] - (
                    0 if p.cell is not None else lines[0]["vertpos"]
                )
                pos_y = (top + line["vertsize"] / 2) / HU_PER_MM - size / 2 + dy
                if p.cell is not None:
                    pos_y += cell_top_mm(p.cell)
            else:
                pos_y = -(size - em_mm) / 2 + dy

            n = 1
            while n in used_nums or f"image{n}" in used_ids:
                n += 1
            used_nums.add(n)
            item_id = f"image{n}"
            used_ids.add(item_id)
            entry = f"BinData/image{n}.{ext}"
            additions[entry] = image
            items.append(
                f'<opf:item id="{item_id}" href="{entry}" media-type="{MIME[ext]}" isEmbeded="1"/>'
            )

            max_id += 2
            pic = build_float_pic(
                item_id,
                round(size * HU_PER_MM),
                round(pos_x * HU_PER_MM),
                round(pos_y * HU_PER_MM),
                max_id - 1,
                max_id,
            )
            splices[si].append(
                (
                    run.close_end,
                    f'<{run.prefix}:run charPrIDRef="{run.char_pr}">{pic}</{run.prefix}:run>',
                )
            )

            warnings = []
            if not lines and p.cell is not None:
                warnings.append(
                    "줄 배치가 없거나 더미라 세로 위치가 칸 첫 줄 기준 어림값입니다. fix_namespaces.py 로 한글 줄 배치를 넣은 뒤 찍으세요"
                )
            host_lines = [
                ln for ln in (p.host.lines if p.host else []) if ln["vertsize"] > 0
            ]
            # 본문 줄 배치 vertpos 는 쪽마다 0 에서 다시 시작하므로 표를 담은 문단의 vertpos 가 쪽 안 표 위치다
            table_top = host_lines[0]["vertpos"] / HU_PER_MM if host_lines else 0.0
            if p.cell is not None and table_top + pos_y + size > body_height_mm(xml):
                # 한글은 세로 위치를 표 위(첫 쪽)에서 재므로 쪽을 넘는 칸의 뒤쪽 문구에는 도장이 앞 쪽에 걸리거나 사라진다
                warnings.append(
                    "칸이 쪽을 넘을 만큼 길어 도장이 앞 쪽에 찍히거나 보이지 않을 수 있습니다. PDF 로 확인하세요"
                )
            if p.has_tab:
                warnings.append(
                    "탭이 든 문단이라 가로 위치가 어림값입니다(--dx 로 보정)"
                )
            if p.has_break:
                warnings.append(
                    "줄바꿈이 든 문단이라 세로 위치가 어긋날 수 있습니다(--dy 로 보정)"
                )
            if p.outer:
                warnings.append(
                    "표 속 표 칸이라 칸 여백과 정렬이 어림값입니다(--dx 로 보정)"
                )
            if p.in_textbox:
                warnings.append("글상자 안이라 위치가 어림값입니다(--dx, --dy 로 보정)")
            placed.append(
                {
                    "occurrence": occ,
                    "section": si,
                    "mode": m,
                    "x_mm": round(pos_x, 2),
                    "y_mm": round(pos_y, 2),
                    "size_mm": round(size, 2),
                    "entry": entry,
                    **({"warnings": warnings} if warnings else {}),
                }
            )

        for si, edits in enumerate(splices):
            for pos, text in sorted(edits, key=lambda e: e[0], reverse=True):
                secs[si] = secs[si][:pos] + text + secs[si][pos:]
        if hpf_name and items and "</opf:manifest>" in hpf:
            hpf = hpf.replace("</opf:manifest>", "".join(items) + "</opf:manifest>")

        changed = {
            n: secs[i].encode("utf-8") for i, n in enumerate(sec_names) if splices[i]
        }
        if hpf_name and items:
            changed[hpf_name] = hpf.encode("utf-8")
        tmp = dst + ".tmp"
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zo:
            for info in zi.infolist():
                data = changed.get(info.filename, None)
                if data is None:
                    data = zi.read(info.filename)
                ct = (
                    zipfile.ZIP_STORED
                    if info.filename == "mimetype"
                    else zipfile.ZIP_DEFLATED
                )
                zo.writestr(info, data, compress_type=ct)
            for name, data in additions.items():
                zo.writestr(name, data)
    Path(tmp).replace(dst)
    return placed


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="HWPX 도장 날인(문구 위에 글 앞 그림)")
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--image", required=True, help="도장 그림(투명 배경 PNG 권장)")
    ap.add_argument("--anchor", default="(인)", help='찾을 문구(기본 "(인)")')
    ap.add_argument(
        "--occurrence",
        default="0",
        help="몇 번째 등장인지(0부터). 0,2 처럼 여럿, all 은 전부",
    )
    ap.add_argument(
        "--size",
        type=float,
        default=None,
        help="도장 한 변 mm(기본: 글자 크기의 1.6배, 7~18mm)",
    )
    ap.add_argument(
        "--mode",
        choices=["auto", "overlap", "right"],
        default="overlap",
        help="overlap=문구 위(기본), right=문구 오른쪽, auto=자리가 있으면 right(kordoc 기본)",
    )
    ap.add_argument("--dx", type=float, default=0.0, help="가로 미세 조정 mm")
    ap.add_argument("--dy", type=float, default=0.0, help="세로 미세 조정 mm")
    a = ap.parse_args()

    occ = (
        "all"
        if a.occurrence.strip() == "all"
        else [int(s) for s in a.occurrence.split(",") if s.strip()]
    )
    img = Path(a.image)
    try:
        placed = place_seals(
            a.input,
            a.output,
            img.read_bytes(),
            img.suffix.lstrip(".") or "png",
            a.anchor,
            occ,
            a.size,
            a.mode,
            a.dx,
            a.dy,
        )
    except ValueError as e:
        print(f"오류: {e}", file=sys.stderr)
        return 1
    print(json.dumps(placed, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
