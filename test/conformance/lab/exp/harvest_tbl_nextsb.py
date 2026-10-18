"""정답본(한/글 줄 배치)에서 자리 차지 표(문단 기준, 글자처럼 취급 아님) 하나를 품은 문단 뒤 다음 문단의 위치가
「호스트 문단 윗변 + 오프셋 + 바깥 여백 위아래 + 표 높이」 에 다음 문단 위 간격을 더한 곳인지(더함), 그 안에 묻는지(묻음) 센다.

    python exp/harvest_tbl_nextsb.py

간격 값은 hp:case(HwpUnitChar) 쪽 실제 값을 쓴다. 호스트 윗변 = 호스트 첫 줄 vpos - 호스트 위 간격.
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


def spacing(h, pid, key):
    pp = re.search(rf'<hh:paraPr id="{pid}"[\s\S]*?</hh:paraPr>', h).group(0)
    case = pp.split("<hp:default>")[0]  # hp:case 쪽(실제 값)
    m = re.search(rf'<hc:{key} value="(-?\d+)"', case)
    return int(m.group(1)) if m else 0


stat = collections.Counter()
samples = collections.defaultdict(list)
for f in sorted(glob.glob(str(OUT / "oracle" / "*.hwpx"))):
    z = zipfile.ZipFile(f)
    h = z.read("Contents/header.xml").decode("utf-8", "replace")
    for name in sorted(
        n for n in z.namelist() if re.match(r"Contents/section\d+\.xml", n)
    ):
        root = etree.fromstring(z.read(name))
        ps = [p for p in root if p.tag == f"{HP}p"]
        for i, p in enumerate(ps[:-1]):
            tbls = p.findall(f"{HP}run/{HP}tbl")
            if len(tbls) != 1 or p.findall(f"{HP}run/{HP}pic"):
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
            if not ls or not nx:
                continue
            host, nxt = int(ls[0].get("vertpos")), int(nx[0].get("vertpos"))
            if nxt <= host:
                continue
            last = ls[-1]
            text_bottom = (
                int(last.get("vertpos"))
                + int(last.get("vertsize"))
                + int(last.get("spacing"))
            )
            om = tb.find(f"{HP}outMargin")
            top = host - spacing(h, p.get("paraPrIDRef"), "prev")
            obj_bottom = (
                top
                + int(pos.get("vertOffset"))
                + int(om.get("top"))
                + int(om.get("bottom"))
                + int(tb.find(f"{HP}sz").get("height"))
            )
            if text_bottom > obj_bottom:
                continue  # 글이 표보다 길다
            nsb = spacing(h, ps[i + 1].get("paraPrIDRef"), "prev")
            if nsb == 0:
                continue
            has_text = bool(
                "".join(
                    t.text or ""
                    for r in p.findall(f"{HP}run")
                    for t in r.findall(f"{HP}t")
                ).strip()
            )
            d = nxt - obj_bottom
            kind = "묻음" if d == 0 else ("더함" if d == nsb else "기타")
            stat[(has_text, kind)] += 1
            samples[(has_text, kind)].append((Path(f).stem, i, nsb, d))
for k, n in sorted(stat.items()):
    print("글 있는 호스트" if k[0] else "빈 호스트", k[1], n, samples[k][:4])
