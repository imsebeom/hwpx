"""한/글 새 조판(out/fresh/rt)에서 자리 차지 표(문단 기준, 글자처럼 취급 아님, 오프셋 ≥ 0)와 글자처럼 취급 표를 함께 품은 문단의 첫 줄이
그 자리 차지 표 아래로 밀리는지 센다.

    python exp/harvest_ownfloat_push.py

밀림 = 첫 줄 vpos 가 「앞 문단 끝 + 위 간격 + 오프셋 + 바깥 여백 위아래 + 표 높이」와 같다(±40). 안 밀림 = 앞 문단 끝 + 위 간격과 같다.
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
        ps = [p for p in etree.fromstring(z.read(name)) if p.tag == f"{HP}p"]
        for i, p in enumerate(ps):
            tbls = p.findall(f"{HP}run/{HP}tbl")
            floats = [
                t
                for t in tbls
                if t.find(f"{HP}pos").get("treatAsChar") == "0"
                and t.get("textWrap") == "TOP_AND_BOTTOM"
                and t.find(f"{HP}pos").get("vertRelTo") == "PARA"
            ]
            tacs = [t for t in tbls if t.find(f"{HP}pos").get("treatAsChar") == "1"]
            if len(floats) != 1 or not tacs:
                continue
            fl = floats[0]
            off = int(fl.find(f"{HP}pos").get("vertOffset"))
            if off > 2**31:
                continue
            ls = p.findall(f"{HP}linesegarray/{HP}lineseg")
            if not ls:
                continue
            v = int(ls[0].get("vertpos"))
            sb = spacing(h, p.get("paraPrIDRef"), "prev")
            if i == 0:
                start = 0
            else:
                pl = ps[i - 1].findall(f"{HP}linesegarray/{HP}lineseg")
                if not pl:
                    continue
                last = pl[-1]
                start = (
                    int(last.get("vertpos"))
                    + int(last.get("vertsize"))
                    + int(last.get("spacing"))
                    + spacing(h, ps[i - 1].get("paraPrIDRef"), "next")
                )
                if v < int(last.get("vertpos")):
                    continue
            om = fl.find(f"{HP}outMargin")
            box = (
                off
                + int(om.get("top"))
                + int(om.get("bottom"))
                + int(fl.find(f"{HP}sz").get("height"))
            )
            if abs(v - (start + sb + box)) <= 40:
                kind = "밀림"
            elif abs(v - (start + sb)) <= 40:
                kind = "안 밀림"
            else:
                kind = "기타"
            stat[kind] += 1
            ex[kind].append((f.stem, name[-12:], i, v, start + sb, box))
for k, n in stat.items():
    print(k, n, ex[k][:5])
