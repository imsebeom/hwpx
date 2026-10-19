"""한/글 새 조판(out/fresh/rt)에서 한 줄짜리 글자처럼 취급 개체(그림, 도형, 묶음 — 위아래 배치 아님) 문단이 쪽 끝에 걸린 경우를 센다.
엔진의 Task #409 top-fit(시작이 본문 안이면 60px 까지 넘쳐 담는다)이 한/글과 맞는지 본다.

    python exp/harvest_atomic_fit.py

- 넘김: 이 문단 첫 줄이 새 쪽(vpos 되감김)이고 앞 문단 끝이 본문 안인데, 줄 높이를 더하면 본문을 넘는다
- 담음: 같은 쪽인데 줄 바닥(vpos + 줄 높이)이 본문을 넘는다(넘쳐 담음)
1단 구역, 본문 = 쪽 높이 − 위, 아래, 머리말, 꼬리말 여백.
"""

import re
import sys
import zipfile
from pathlib import Path

from lxml import etree

sys.stdout.reconfigure(encoding="utf-8")
HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
OUT = Path(__file__).resolve().parent.parent.parent / "out"
OBJ = (
    "pic",
    "container",
    "rect",
    "ellipse",
    "line",
    "polygon",
    "curve",
    "arc",
    "ole",
    "chart",
)


def atomic(p):
    found = False
    for r in p.findall(f"{HP}run"):
        for el in r:
            tag = etree.QName(el).localname
            if tag == "tbl":
                return False
            if tag in OBJ:
                pos = el.find(f"{HP}pos")
                if (
                    pos is None
                    or pos.get("treatAsChar") != "1"
                    or el.get("textWrap") == "TOP_AND_BOTTOM"
                ):
                    return False
                found = True
    return found


moved, kept = [], []
for f in sorted((OUT / "fresh" / "rt").glob("*.hwpx")):
    z = zipfile.ZipFile(f)
    for name in sorted(
        n for n in z.namelist() if re.match(r"Contents/section\d+\.xml", n)
    ):
        raw = z.read(name)
        if re.search(rb'colCount="[2-9]"', raw):
            continue
        pg = re.search(rb'<hp:pagePr[^>]*height="(\d+)"', raw)
        mg = re.search(rb"<hp:margin ([^>]*)>", raw)
        if not pg or not mg:
            continue
        mv = {k.decode(): int(v) for k, v in re.findall(rb'(\w+)="(\d+)"', mg.group(1))}
        body = int(pg.group(1)) - mv["top"] - mv["bottom"] - mv["header"] - mv["footer"]
        ps = [p for p in etree.fromstring(raw) if p.tag == f"{HP}p"]
        for i in range(1, len(ps)):
            p, prev = ps[i], ps[i - 1]
            ls = p.findall(f"{HP}linesegarray/{HP}lineseg")
            pls = prev.findall(f"{HP}linesegarray/{HP}lineseg")
            if len(ls) != 1 or not pls or not atomic(p) or p.get("pageBreak") == "1":
                continue
            v, lh = int(ls[0].get("vertpos")), int(ls[0].get("vertsize"))
            last = pls[-1]
            end = (
                int(last.get("vertpos"))
                + int(last.get("vertsize"))
                + int(last.get("spacing"))
            )
            rec = (f.stem, name[-12:], i, end, lh, body, v)
            if v < int(last.get("vertpos")) and end < body and end + lh > body:
                moved.append(rec)
            elif v >= int(last.get("vertpos")) and v + lh > body:
                kept.append(rec)
print("넘김", len(moved), moved[:8])
print("넘쳐 담음", len(kept), kept[:8])
