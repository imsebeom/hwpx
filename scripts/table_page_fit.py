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


def _table_height(tbl: str) -> int:
    """표 높이. sz가 있으면 그 값, 없으면 행 높이 합."""
    sz = re.search(r'<hp:sz\b[^>]*\bheight="(\d+)"', tbl)
    if sz:
        return int(sz.group(1))
    rows = re.findall(r"<hp:tr>.*?</hp:tr>", tbl, re.S)
    total = 0
    for r in rows:
        hs = re.findall(r'<hp:cellSz\b[^>]*\bheight="(\d+)"', r)
        if hs:
            total += max(int(x) for x in hs)
    return total


def analyze(path: str | Path) -> list[dict]:
    """문서의 표마다 현재 설정과 권장 설정을 낸다."""
    out: list[dict] = []
    with zipfile.ZipFile(path) as zf:
        sections = sorted(
            n
            for n in zf.namelist()
            if n.startswith("Contents/section") and n.endswith(".xml")
        )
        for name in sections:
            xml = zf.read(name).decode("utf-8", "replace")
            avail = body_height(xml)
            for idx, m in enumerate(re.finditer(r"<hp:tbl\b.*?</hp:tbl>", xml, re.S)):
                tbl = m.group(0)
                open_tag = re.match(r"<hp:tbl\b[^>]*>", tbl).group()
                h = _table_height(tbl)
                rows = len(re.findall(r"<hp:tr>", tbl))
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
                        "current_repeatHeader": cur_repeat.group(1) if cur_repeat else None,
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
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(
        target, "w", zipfile.ZIP_DEFLATED
    ) as zout:
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
    for i, m in enumerate(re.finditer(r"<hp:tbl\b.*?</hp:tbl>", xml, re.S)):
        plan = next((p for p in plans if p["index"] == i), None)
        if plan is None:
            continue
        tbl = m.group(0)
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

        body = tbl[open_m.end():]
        if plan.get("danger") and plan["current_treatAsChar"] == "1":
            body = body.replace(
                '<hp:pos treatAsChar="1"', '<hp:pos treatAsChar="0"', 1
            )

        if new_tag != open_tag or body != tbl[open_m.end():]:
            changed += 1
            pieces.append(xml[last : m.start()])
            pieces.append(new_tag + body)
            last = m.end()

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
