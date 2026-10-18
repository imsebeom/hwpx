"""정답본 본문 문단의 줄 배치와 간격을 찍는다.

    python exp/paradump.py d010 15 19 [section0]

열: 문단 번호, 위 간격, 아래 간격, 줄마다 (vpos, 높이, 줄 간격), 표, 그림 여부, 글 앞부분.
"""

import re
import sys
import zipfile
from pathlib import Path

from lxml import etree

sys.stdout.reconfigure(encoding="utf-8")
HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
OUT = Path(__file__).resolve().parent.parent.parent / "out"


def spacing(h, pid, key):
    pp = re.search(rf'<hh:paraPr id="{pid}"[\s\S]*?</hh:paraPr>', h).group(0)
    m = re.search(rf'<hc:{key} value="(-?\d+)"', pp.split("<hp:default>")[0])
    return int(m.group(1)) if m else 0


doc, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
sec = sys.argv[4] if len(sys.argv) > 4 else "section0"
z = zipfile.ZipFile(OUT / "oracle" / f"{doc}.hwpx")
h = z.read("Contents/header.xml").decode("utf-8", "replace")
raw = z.read(f"Contents/{sec}.xml")
pg = re.search(rb"<hp:pagePr[^>]*>", raw).group(0).decode()
mg = re.search(rb"<hp:margin [^>]*>", raw).group(0).decode()
print(pg)
print(mg)
root = etree.fromstring(raw)
ps = [p for p in root if p.tag == f"{HP}p"]
for i in range(a, min(b + 1, len(ps))):
    p = ps[i]
    pid = p.get("paraPrIDRef")
    segs = [
        (int(s.get("vertpos")), int(s.get("vertsize")), int(s.get("spacing")))
        for s in p.findall(f"{HP}linesegarray/{HP}lineseg")
    ]
    kinds = "".join(
        k
        for k, tag in (("T", "tbl"), ("P", "pic"), ("C", "ctrl"))
        if p.find(f".//{HP}{tag}") is not None
    )
    text = "".join(t.text or "" for t in p.iter(f"{HP}t"))[:24]
    print(
        i,
        "sb",
        spacing(h, pid, "prev"),
        "sa",
        spacing(h, pid, "next"),
        kinds,
        p.get("pageBreak"),
        segs[:3],
        "…" if len(segs) > 3 else "",
        segs[-1] if len(segs) > 3 else "",
        repr(text),
    )
