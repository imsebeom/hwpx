#!/usr/bin/env python3
"""표가 페이지 경계에서 깨지지 않도록 쪽 나눔 설정을 진단·적용한다.

KS X 6101:2024 표 194가 정의하는 tbl@pageBreak 세 값을 표 높이에 맞춰 고른다.

    NONE   표를 나누지 않는다 → 표 전체가 다음 쪽으로 넘어간다
    TABLE  표는 나누되 셀은 나누지 않는다
    CELL   셀 내부 텍스트까지 나눈다 (한컴 기본값)

한 쪽에 들어가는 표를 CELL로 두면 페이지 끝에서 어정쩡하게 쪼개진다. 반대로
여러 쪽에 걸치는 표를 NONE으로 두면 아예 배치되지 못한다. 표 높이와 본문
영역 높이를 비교해 판단한다. 나뉘는 표에는 repeatHeader="1"을 함께 준다
(제목 행이 다음 쪽에도 반복된다).

사용:
    python table_page_fit.py 문서.hwpx              # 진단만
    python table_page_fit.py 문서.hwpx --apply      # 권장값 적용(제자리)
    python table_page_fit.py 문서.hwpx --apply -o 새파일.hwpx
"""

from __future__ import annotations

import os
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

STORED_ENTRIES = ("mimetype", "version.xml")

# 표가 본문 높이의 이 비율을 넘으면 "쪽을 넘길 수 있다"고 본다.
# 표 앞에 본문이 얼마나 있느냐에 따라 시작 위치가 달라지므로 여유를 둔다.
SPLIT_RATIO = 0.45


def body_height(section_xml: str) -> int | None:
    """본문 영역 높이(HWPUNIT). 용지 높이에서 상하 여백과 머리말·꼬리말을 뺀다."""
    pp = re.search(r"<hp:pagePr\b[^>]*>", section_xml)
    mg = re.search(r"<hp:margin\b[^>]*/>", section_xml)
    if not pp or not mg:
        return None
    h = re.search(r'height="(\d+)"', pp.group())
    if not h:
        return None
    d = {k: int(v) for k, v in re.findall(r'(\w+)="(\d+)"', mg.group())}
    return (
        int(h.group(1))
        - d.get("top", 0)
        - d.get("bottom", 0)
        - d.get("header", 0)
        - d.get("footer", 0)
    )


# 칸 글 양으로 높이를 어림할 때 쓰는 값. 크게 잡을수록 안전한 TABLE 쪽으로 기운다.
LINE_SPACING = 1.6  # 줄 간격 160%
NARROW_GLYPH = 0.55  # 한글, 한자가 아닌 글자의 폭(글자 크기 대비)


def char_heights(header_xml: str) -> dict[str, int]:
    """charPr id → 글자 크기(HWPUNIT)."""
    return {
        m.group(1): int(m.group(2))
        for m in re.finditer(
            r'<hh:charPr\b[^>]*\bid="(\d+)"[^>]*\bheight="(\d+)"', header_xml
        )
    }


def top_level(xml: str, tag: str) -> list[tuple[int, int]]:
    """xml 안 바깥쪽 <hp:{tag}> 요소의 (시작, 끝) 위치. 같은 이름 요소가 안에 들어 있어도 짝을 맞춘다.

    `<hp:tbl\\b.*?</hp:tbl>` 같은 짧은 일치는 표 안 표의 닫는 태그에서 바깥 표를 끊는다. 그러면 41행 바깥 표를
    안쪽 표의 5행으로 보고 NONE 을 권해, 한글에서 40행 중 25행만 그려졌다(2026-10-17 실측).
    """
    out, depth, start = [], 0, 0
    for m in re.finditer(rf"<hp:{tag}\b[^>]*?(/?)>|</hp:{tag}>", xml):
        if m.group(0).startswith("</"):
            depth -= 1
            if depth == 0:
                out.append((start, m.end()))
        elif m.group(1) == "/":
            if depth == 0:
                out.append((m.start(), m.end()))
        else:
            if depth == 0:
                start = m.start()
            depth += 1
    return out


def _own_cell_part(tc: str) -> str:
    """칸 자신의 cellAddr, cellSpan, cellSz, cellMargin 이 있는 꼬리. 칸 내용(subList) 안의 표 속성을 피한다."""
    i = tc.rfind("</hp:subList>")
    return tc[i:] if i >= 0 else tc


def _cell_content_height(tc: str, heights: dict[str, int]) -> int:
    """칸 글을 칸 폭에 흘려 넣은 높이 어림값과, 한글이 남긴 줄 배치 캐시로 잰 높이 중 큰 값."""
    own = _own_cell_part(tc)
    w = re.search(r'<hp:cellSz\b[^>]*\bwidth="(\d+)"', own)
    mg = re.search(r"<hp:cellMargin\b[^>]*/>", own)
    m = {k: int(v) for k, v in re.findall(r'(\w+)="(\d+)"', mg.group())} if mg else {}
    inner_w = max(
        (int(w.group(1)) if w else 0) - m.get("left", 510) - m.get("right", 510), 1000
    )
    est = 0
    for p in re.findall(r"<hp:p\b.*?</hp:p>", tc, re.S):
        size, units = 1000, 0.0
        for cp, body in re.findall(
            r'<hp:run\b[^>]*\bcharPrIDRef="(\d+)"[^>]*>(.*?)</hp:run>', p, re.S
        ):
            h = heights.get(cp, 1000)
            size = max(size, h)
            text = "".join(re.findall(r"<hp:t>([^<]*)</hp:t>", body))
            units += sum(h if ord(c) >= 0x2E80 else h * NARROW_GLYPH for c in text)
        lines = max(1, -(-int(units) // inner_w))
        est += int(lines * size * LINE_SPACING)
    # 한글이 저장한 문서는 칸 문단마다 줄 위치(vertpos)와 줄 높이(vertsize)가 남아 있다
    segs = [
        int(a) + int(b)
        for a, b in re.findall(
            r'<hp:lineseg\b[^>]*\bvertpos="(\d+)"[^>]*\bvertsize="(\d+)"', tc
        )
    ]
    measured = max(segs) if segs else 0
    return max(est, measured) + m.get("top", 141) + m.get("bottom", 141)


def _table_height(tbl: str, heights: dict[str, int] | None = None) -> int:
    """표 높이. 적힌 값(hp:sz)과 행마다 cellSz, 칸 글 양으로 어림한 높이의 합 중 큰 값.

    적힌 hp:sz height만 믿으면 안 된다. 한글은 이 값을 읽지 않고 다시 계산하며(2026-10-17 실측),
    쪽을 넘는 표를 저장할 때는 첫 쪽 조각의 높이만 적는다(41행 표가 15,320). 생성기(md2hwpx)는
    내용과 무관하게 2,400 × 행 수를 적는다. 어느 쪽이든 실제보다 작게 보면 NONE을 권해 넘친 행이 사라진다.
    """
    heights = heights or {}
    sz = re.search(r'<hp:sz\b[^>]*\bheight="(\d+)"', tbl)
    total = 0
    for ra, rb in top_level(tbl, "tr"):
        r = tbl[ra:rb]
        row = 0
        for ca, cb in top_level(r, "tc"):
            tc = r[ca:cb]
            own = _own_cell_part(tc)
            span = re.search(r'\browSpan="(\d+)"', own)
            if span and int(span.group(1)) > 1:
                continue  # 여러 행에 걸친 칸은 한 행 높이로 보지 않는다(규칙 33)
            cs = re.search(r'<hp:cellSz\b[^>]*\bheight="(\d+)"', own)
            row = max(
                row, int(cs.group(1)) if cs else 0, _cell_content_height(tc, heights)
            )
        total += row
    return max(int(sz.group(1)) if sz else 0, total)


def analyze(path: str | Path) -> list[dict]:
    """문서의 표마다 현재 설정과 권장 설정을 낸다."""
    out: list[dict] = []
    with zipfile.ZipFile(path) as zf:
        sections = sorted(
            n
            for n in zf.namelist()
            if n.startswith("Contents/section") and n.endswith(".xml")
        )
        names = set(zf.namelist())
        heights = (
            char_heights(zf.read("Contents/header.xml").decode("utf-8", "replace"))
            if "Contents/header.xml" in names
            else {}
        )
        for name in sections:
            xml = zf.read(name).decode("utf-8", "replace")
            avail = body_height(xml)
            for idx, (ta, tb) in enumerate(top_level(xml, "tbl")):
                tbl = xml[ta:tb]
                open_tag = re.match(r"<hp:tbl\b[^>]*>", tbl).group()
                h = _table_height(tbl, heights)
                rows = len(top_level(tbl, "tr"))
                cur_break = re.search(r'\bpageBreak="(\w+)"', open_tag)
                cur_repeat = re.search(r'\brepeatHeader="(\d+)"', open_tag)
                pos = re.search(r"<hp:pos\b[^>]*/>", tbl)
                as_char = None
                if pos:
                    tac = re.search(r'\btreatAsChar="(\d)"', pos.group())
                    as_char = tac.group(1) if tac else None
                ratio = (h / avail) if avail else None

                if avail is None:
                    rec_break, why = "TABLE", "용지 설정을 읽지 못해 안전한 값 선택"
                elif h >= avail:
                    rec_break, why = (
                        "TABLE",
                        f"표 높이가 본문 영역({avail})보다 커서 반드시 나뉜다",
                    )
                elif ratio >= SPLIT_RATIO:
                    rec_break, why = (
                        "TABLE",
                        f"본문 높이의 {ratio:.0%}라 시작 위치에 따라 나뉠 수 있다",
                    )
                else:
                    rec_break, why = (
                        "NONE",
                        f"본문 높이의 {ratio:.0%}라 한 쪽에 들어간다. 쪼개지 말고 통째로 넘긴다",
                    )
                rec_repeat = "1" if rec_break == "TABLE" and rows > 1 else None

                # 글자처럼 취급된 표는 한 문단 안에 갇혀 쪽을 넘기지 못한다.
                # 쪽을 넘겨야 하는 표라면 넘친 행이 통째로 사라진다(무언의 데이터 손실).
                danger = None
                if as_char == "1" and avail and h > avail:
                    danger = (
                        'treatAsChar="1"인데 표가 본문 높이를 넘는다 '
                        "— 쪽을 넘기지 못해 넘친 행이 사라진다. 0으로 바꿔야 한다"
                    )

                out.append(
                    {
                        "section": name,
                        "index": idx,
                        "rows": rows,
                        "height": h,
                        "avail": avail,
                        "ratio": ratio,
                        "current_pageBreak": cur_break.group(1) if cur_break else None,
                        "current_repeatHeader": cur_repeat.group(1)
                        if cur_repeat
                        else None,
                        "current_treatAsChar": as_char,
                        "recommend_treatAsChar": "0" if danger else as_char,
                        "recommend_pageBreak": rec_break,
                        "recommend_repeatHeader": rec_repeat,
                        "reason": why,
                        "danger": danger,
                    }
                )
    return out


def apply(src: str | Path, dst: str | Path | None = None) -> dict:
    """권장 설정을 문서에 적용한다."""
    src = Path(src)
    dst = Path(dst) if dst else src
    plans = analyze(src)
    by_section: dict[str, list[dict]] = {}
    for p in plans:
        by_section.setdefault(p["section"], []).append(p)

    same = dst.resolve() == src.resolve()
    tmpdir = Path(tempfile.mkdtemp(prefix="hwpx-tablefit-")) if same else None
    target = (tmpdir / "out.hwpx") if tmpdir else dst

    changed = 0
    with (
        zipfile.ZipFile(src) as zin,
        zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zout,
    ):
        for info in zin.infolist():
            data = zin.read(info.filename)
            plans_here = by_section.get(info.filename)
            if plans_here:
                xml = data.decode("utf-8")
                xml, n = _rewrite(xml, plans_here)
                changed += n
                data = xml.encode("utf-8")
            mode = (
                zipfile.ZIP_STORED
                if info.filename in STORED_ENTRIES
                else info.compress_type
            )
            out_info = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            out_info.compress_type = mode
            out_info.external_attr = info.external_attr
            zout.writestr(out_info, data)

    if tmpdir:
        shutil.move(str(target), str(dst))
        shutil.rmtree(tmpdir, ignore_errors=True)
    return {"changed": changed, "tables": len(plans)}


def _rewrite(xml: str, plans: list[dict]) -> tuple[str, int]:
    changed = 0
    pieces: list[str] = []
    last = 0
    for i, (ta, tb) in enumerate(top_level(xml, "tbl")):
        plan = next((p for p in plans if p["index"] == i), None)
        if plan is None:
            continue
        tbl = xml[ta:tb]
        open_m = re.match(r"<hp:tbl\b[^>]*>", tbl)
        open_tag = open_m.group()
        new_tag = open_tag

        want_break = plan["recommend_pageBreak"]
        if plan["current_pageBreak"] != want_break:
            if plan["current_pageBreak"] is not None:
                new_tag = re.sub(
                    r'\bpageBreak="\w+"', f'pageBreak="{want_break}"', new_tag, count=1
                )
            else:
                new_tag = new_tag[:-1] + f' pageBreak="{want_break}">'

        want_repeat = plan["recommend_repeatHeader"]
        if want_repeat is not None and plan["current_repeatHeader"] != want_repeat:
            if plan["current_repeatHeader"] is not None:
                new_tag = re.sub(
                    r'\brepeatHeader="\d+"',
                    f'repeatHeader="{want_repeat}"',
                    new_tag,
                    count=1,
                )
            else:
                new_tag = new_tag[:-1] + f' repeatHeader="{want_repeat}">'

        body = tbl[open_m.end() :]
        if plan.get("danger") and plan["current_treatAsChar"] == "1":
            body = body.replace('<hp:pos treatAsChar="1"', '<hp:pos treatAsChar="0"', 1)

        if new_tag != open_tag or body != tbl[open_m.end() :]:
            changed += 1
            pieces.append(xml[last:ta])
            pieces.append(new_tag + body)
            last = tb

    pieces.append(xml[last:])
    return "".join(pieces), changed


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="표 쪽 나눔 설정 진단·적용")
    ap.add_argument("input")
    ap.add_argument("--apply", action="store_true", help="권장값을 적용한다")
    ap.add_argument("-o", "--output", help="출력 경로 (생략 시 제자리 수정)")
    a = ap.parse_args()

    plans = analyze(a.input)
    if not plans:
        print("표가 없다.")
        return

    print(f"표 {len(plans)}개")
    for p in plans:
        cur = f"{p['current_pageBreak'] or '-'}/{p['current_repeatHeader'] or '-'}"
        rec = f"{p['recommend_pageBreak']}/{p['recommend_repeatHeader'] or '-'}"
        mark = " " if cur == rec else "→"
        ratio = f"{p['ratio']:.0%}" if p["ratio"] is not None else "?"
        print(
            f"  [{p['index']}] {p['rows']}행 높이 {p['height']:,} (본문의 {ratio})"
            f"  {cur} {mark} {rec}"
        )
        print(f"       {p['reason']}")
        if p.get("danger"):
            print(f"       ⚠ {p['danger']}")

    if a.apply:
        r = apply(a.input, a.output)
        where = a.output or a.input
        print(f"\n{r['changed']}개 표 수정 → {where}")
    else:
        need = sum(
            1
            for p in plans
            if (p["current_pageBreak"], p["current_repeatHeader"])
            != (p["recommend_pageBreak"], p["recommend_repeatHeader"])
        )
        if need:
            print(f"\n{need}개 표가 권장값과 다르다. --apply로 적용한다.")


if __name__ == "__main__":
    main()
