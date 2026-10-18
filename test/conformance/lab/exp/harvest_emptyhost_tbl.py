"""정답본(한/글 저장 줄 배치)에서 글 없는 문단에 자리 차지 표 하나만 든 경우를 모아, 다음 문단까지의 전진과
「오프셋 + 높이 + 바깥 여백 위아래」의 차이를 본다(d268 p64 는 -400, p67 형은 0).

    python exp/harvest_emptyhost_tbl.py
"""

import collections
import glob
import re
import sys
import zipfile
from pathlib import Path

from lxml import etree

sys.stdout.reconfigure(encoding="utf-8")
HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
OUT = Path(__file__).resolve().parent.parent.parent / "out"
rows = []
for f in sorted(glob.glob(str(OUT / "oracle" / "*.hwpx"))):
    z = zipfile.ZipFile(f)
    h = z.read("Contents/header.xml").decode("utf-8", "replace")
    for name in sorted(
        n for n in z.namelist() if re.match(r"Contents/section\d+\.xml", n)
    ):
        root = etree.fromstring(z.read(name))
        ps = [p for p in root if p.tag == f"{HP}p"]
        for i, p in enumerate(ps[:-1]):
            text = "".join(
                t.text or ""
                for t in p.iter(f"{HP}t")
                if not any(a.tag == f"{HP}tbl" for a in t.iterancestors())
            )
            tbls = [t for t in p.findall(f"{HP}run/{HP}tbl")]
            if (
                text.strip()
                or len(tbls) != 1
                or len(p.findall(f"{HP}run/{HP}ctrl"))
                or len(p.findall(f"{HP}run/{HP}pic"))
            ):
                continue
            tb = tbls[0]
            pos = tb.find(f"{HP}pos")
            if (
                pos.get("treatAsChar") != "0"
                or tb.get("textWrap") != "TOP_AND_BOTTOM"
                or pos.get("vertRelTo") != "PARA"
            ):
                continue
            ls = p.findall(f"{HP}linesegarray/{HP}lineseg")
            nx = ps[i + 1].findall(f"{HP}linesegarray/{HP}lineseg")
            if len(ls) != 1 or not nx:
                continue
            host, nxt = int(ls[0].get("vertpos")), int(nx[0].get("vertpos"))
            if nxt <= host:
                continue  # 쪽이 바뀜
            om = tb.find(f"{HP}outMargin")
            off = int(pos.get("vertOffset"))
            hgt = int(tb.find(f"{HP}sz").get("height"))
            top, bot = int(om.get("top")), int(om.get("bottom"))
            # 다음 문단 위 간격
            pid = ps[i + 1].get("paraPrIDRef")
            pp = re.search(rf'<hh:paraPr id="{pid}"[\s\S]*?</hh:paraPr>', h).group(0)
            case = pp.split("<hp:default>")[-1]
            prev = re.search(r'<hc:prev value="(-?\d+)"', case)
            sb = int(prev.group(1)) if prev else 0
            line = int(ls[0].get("vertsize")) + int(ls[0].get("spacing"))
            hp_ = re.search(rf'<hh:paraPr id="{p.get("paraPrIDRef")}"[\s\S]*?</hh:paraPr>', h).group(0).split("<hp:default>")[-1]
            hprev = re.search(r'<hc:prev value="(-?\d+)"', hp_)
            host_sb = int(hprev.group(1)) if hprev else 0
            d = (nxt - host) - (off + hgt + top + bot)
            rows.append((Path(f).stem, name[-12:], i, off, top, bot, sb, line, d, host_sb))
print("표본", len(rows))
by = collections.Counter((r[3] == 0, r[8]) for r in rows)
for (zero, d), n in by.most_common(15):
    print(f"오프셋0={zero} 차={d} : {n}")
small = [r for r in rows if abs(r[8]) < 2000]
print("차 = -호스트 위 간격 인 표본", sum(1 for r in small if r[8] == -r[9]), "/", len(small))
print("오프셋 0 이고 차가 0 아닌 예:")
for r in [r for r in rows if r[3] == 0 and r[8] != 0][:15]:
    print("  ", r)
