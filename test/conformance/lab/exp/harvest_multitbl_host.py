"""새 정답본에서 글 없는 문단에 자리 차지 표(문단 기준)가 둘 이상 든 경우, 호스트 줄 위치를 첫 표와 견준다.

    python exp/harvest_multitbl_host.py [폴더]   (기본 out/fresh/rt)

D = 호스트 줄 vpos − 앞 문단 끝 − (첫 표 오프셋 + 바깥 여백 위아래 + 높이), E = 다음 문단 vpos − 호스트 줄 vpos − 호스트 줄 높이와 줄 간격.
D = 0 이면 호스트 줄이 첫 표 바로 아래, E = 0 이면 다음 문단이 호스트 줄 바로 아래.
"""

import glob
import re
import sys
import zipfile
from pathlib import Path

from lxml import etree

sys.stdout.reconfigure(encoding="utf-8")
HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
OUT = Path(__file__).resolve().parent.parent.parent / "out"
src = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT / "fresh" / "rt"


def segs(p):
    return p.findall(f"{HP}linesegarray/{HP}lineseg")


for f in sorted(glob.glob(str(src / "*.hwpx"))):
    z = zipfile.ZipFile(f)
    for name in sorted(
        n for n in z.namelist() if re.match(r"Contents/section\d+\.xml", n)
    ):
        root = etree.fromstring(z.read(name))
        ps = [p for p in root if p.tag == f"{HP}p"]
        for i in range(1, len(ps)):
            p = ps[i]
            text = "".join(
                t.text or ""
                for t in p.iter(f"{HP}t")
                if not any(a.tag == f"{HP}tbl" for a in t.iterancestors())
            )
            tbls = [
                t
                for t in p.findall(f"{HP}run/{HP}tbl")
                if t.find(f"{HP}pos").get("treatAsChar") == "0"
                and t.get("textWrap") == "TOP_AND_BOTTOM"
            ]
            if text.strip() or len(tbls) < 2:
                continue
            ls = segs(p)
            pv = segs(ps[i - 1])
            nx = segs(ps[i + 1]) if i + 1 < len(ps) else []
            if not ls:
                continue
            host = int(ls[0].get("vertpos"))
            t0 = tbls[0]
            pos, om = t0.find(f"{HP}pos"), t0.find(f"{HP}outMargin")
            T = (
                int(pos.get("vertOffset"))
                + int(om.get("top"))
                + int(om.get("bottom"))
                + int(t0.find(f"{HP}sz").get("height"))
            )
            prev_end = (
                int(pv[-1].get("vertpos"))
                + int(pv[-1].get("vertsize"))
                + int(pv[-1].get("spacing"))
                if pv
                else None
            )
            start = (
                0
                if p.get("pageBreak") == "1"
                or (prev_end is not None and host < prev_end)
                else prev_end
            )
            L = int(ls[0].get("vertsize")) + int(ls[0].get("spacing"))
            nxt = int(nx[0].get("vertpos")) if nx else None
            D = host - start - T if start is not None else None
            E = nxt - host - L if nxt is not None and nxt > host else None
            info = [
                (
                    t.find(f"{HP}pos").get("vertRelTo"),
                    t.find(f"{HP}pos").get("vertOffset"),
                    t.find(f"{HP}sz").get("height"),
                )
                for t in tbls
            ]
            print(
                Path(f).stem,
                name[-12:],
                i,
                "줄",
                len(ls),
                "폭",
                ls[0].get("horzsize"),
                "D",
                D,
                "E",
                E,
                info,
            )
