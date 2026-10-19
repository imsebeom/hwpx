"""새 정답본에서 글 없는 문단에 어울림(SQUARE) 표 하나만 든 경우, 다음 문단까지의 전진을 표 높이와 견준다.

    python exp/harvest_emptyhost_square.py [폴더]   (기본 out/fresh/rt)

B = 다음 문단 vpos − 호스트 줄 vpos, T = 오프셋 + 바깥 여백 위아래 + 표 높이, L = 호스트 줄 높이 + 줄 간격.
표 너비(바깥 여백 포함)가 줄 폭 이상이면 「꽉 참」(옆에 글이 들어갈 자리가 없다).
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
src = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT / "fresh" / "rt"


def spacing(h, pid):
    pp = re.search(rf'<hh:paraPr id="{pid}"[\s\S]*?</hh:paraPr>', h).group(0)
    case = pp.split("<hp:default>")[0]
    prev = re.search(r'<hc:prev value="(-?\d+)"', case)
    nxt = re.search(r'<hc:next value="(-?\d+)"', case)
    return (int(prev.group(1)) if prev else 0, int(nxt.group(1)) if nxt else 0)


kinds = collections.Counter()
for f in sorted(glob.glob(str(src / "*.hwpx"))):
    z = zipfile.ZipFile(f)
    h = z.read("Contents/header.xml").decode("utf-8", "replace")
    for name in sorted(
        n for n in z.namelist() if re.match(r"Contents/section\d+\.xml", n)
    ):
        root = etree.fromstring(z.read(name))
        ps = [p for p in root if p.tag == f"{HP}p"]
        for i in range(len(ps) - 1):
            p = ps[i]
            text = "".join(
                t.text or ""
                for t in p.iter(f"{HP}t")
                if not any(a.tag == f"{HP}tbl" for a in t.iterancestors())
            )
            tbls = p.findall(f"{HP}run/{HP}tbl")
            if text.strip() or len(tbls) != 1 or p.findall(f"{HP}run/{HP}pic"):
                continue
            tb = tbls[0]
            pos = tb.find(f"{HP}pos")
            if (
                pos.get("treatAsChar") != "0"
                or tb.get("textWrap") != "SQUARE"
                or pos.get("vertRelTo") != "PARA"
            ):
                continue
            ls = p.findall(f"{HP}linesegarray/{HP}lineseg")
            nx = ps[i + 1].findall(f"{HP}linesegarray/{HP}lineseg")
            if len(ls) != 1 or not nx:
                continue
            host, nxt = int(ls[0].get("vertpos")), int(nx[0].get("vertpos"))
            if nxt <= host:
                continue
            om = tb.find(f"{HP}outMargin")
            sz = tb.find(f"{HP}sz")
            T = (
                int(pos.get("vertOffset"))
                + int(om.get("top"))
                + int(om.get("bottom"))
                + int(sz.get("height"))
            )
            L = int(ls[0].get("vertsize")) + int(ls[0].get("spacing"))
            W = int(sz.get("width")) + int(om.get("left")) + int(om.get("right"))
            _, hsa = spacing(h, p.get("paraPrIDRef"))
            nsb, _ = spacing(h, ps[i + 1].get("paraPrIDRef"))
            full = W >= 48000 or int(ls[0].get("horzsize")) == 0
            B = nxt - host
            if B == T:
                k = "B=T"
            elif B == T + hsa + nsb:
                k = "B=T+간격"
            elif B == T + L:
                k = "B=T+줄"
            elif B == T + L + hsa + nsb:
                k = "B=T+줄+간격"
            else:
                k = "기타"
            kinds[(full, k)] += 1
            print(
                Path(f).stem,
                name[-12:],
                i,
                "꽉참" if full else "옆자리",
                k,
                "B",
                B,
                "T",
                T,
                "L",
                L,
                "간격",
                hsa,
                nsb,
                "폭",
                ls[0].get("horzsize"),
            )
for k, n in sorted(kinds.items()):
    print(k, n)
