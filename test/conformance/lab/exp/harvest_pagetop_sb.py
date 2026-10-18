"""한/글 새 조판(out/fresh/rt)에서 쪽 머리(vpos 되감김) 본문 문단의 첫 줄 vpos 가 위 간격과 같은지 센다.

    python exp/harvest_pagetop_sb.py

1단 구역, 첫 문단 제외, 쪽 나누기(pageBreak) 여부를 나눠 센다. 간격은 hp:case(실제 값).
"""

import collections
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


stat = collections.Counter()
ex = collections.defaultdict(list)
for f in sorted((OUT / "fresh" / "rt").glob("*.hwpx")):
    z = zipfile.ZipFile(f)
    h = z.read("Contents/header.xml").decode("utf-8", "replace")
    for name in sorted(
        n for n in z.namelist() if re.match(r"Contents/section\d+\.xml", n)
    ):
        raw = z.read(name)
        if re.search(rb'colCount="[2-9]"', raw):
            continue
        ps = [p for p in etree.fromstring(raw) if p.tag == f"{HP}p"]
        prev = None
        for i, p in enumerate(ps):
            segs = p.findall(f"{HP}linesegarray/{HP}lineseg")
            if not segs:
                continue
            v = int(segs[0].get("vertpos"))
            if prev is not None and v < prev:
                sb = spacing(h, p.get("paraPrIDRef"), "prev")
                if sb > 0:
                    pb = "쪽나눔" if p.get("pageBreak") == "1" else "흐름"
                    kind = (
                        "vpos=위간격" if v == sb else ("vpos=0" if v == 0 else "기타")
                    )
                    stat[(pb, kind)] += 1
                    ex[(pb, kind)].append((f.stem, name[-12:], i, v, sb))
            prev = int(segs[-1].get("vertpos"))
for k, n in sorted(stat.items()):
    print(k, n, ex[k][:4])
