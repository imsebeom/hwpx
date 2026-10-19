"""새 정답본(한/글이 처음부터 조판한 줄 배치)에서 글 없는 문단에 자리 차지 표 하나만 든 경우, 호스트 줄이 표 위에 있는지 아래에 있는지 센다.

    python exp/harvest_emptyhost_line.py [폴더]   (기본 out/fresh/rt)

A = 호스트 줄 vpos − 앞 문단 끝(앞 문단 마지막 줄 vpos + 높이 + 줄 간격), B = 다음 문단 vpos − 호스트 줄 vpos.
T = 오프셋 + 바깥 여백 위아래 + 표 높이, L = 호스트 줄 높이 + 줄 간격.
- 아래: A ≈ T(호스트 줄이 표 아래), B ≈ L
- 위: A ≈ 0, B ≈ T
간격(위, 아래)은 hp:case 쪽 실제 값으로 따로 찍는다.
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


rows = []
for f in sorted(glob.glob(str(src / "*.hwpx"))):
    z = zipfile.ZipFile(f)
    h = z.read("Contents/header.xml").decode("utf-8", "replace")
    for name in sorted(
        n for n in z.namelist() if re.match(r"Contents/section\d+\.xml", n)
    ):
        root = etree.fromstring(z.read(name))
        ps = [p for p in root if p.tag == f"{HP}p"]
        for i in range(1, len(ps) - 1):
            p = ps[i]
            text = "".join(
                t.text or ""
                for t in p.iter(f"{HP}t")
                if not any(a.tag == f"{HP}tbl" for a in t.iterancestors())
            )
            tbls = p.findall(f"{HP}run/{HP}tbl")
            if (
                text.strip()
                or len(tbls) != 1
                or p.findall(f"{HP}run/{HP}ctrl")
                or p.findall(f"{HP}run/{HP}pic")
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
            pv = ps[i - 1].findall(f"{HP}linesegarray/{HP}lineseg")
            nx = ps[i + 1].findall(f"{HP}linesegarray/{HP}lineseg")
            if len(ls) != 1 or not nx or not pv:
                continue
            # 앞 문단이 표나 개체를 품으면 끝 위치를 줄로 알 수 없다
            if ps[i - 1].findall(f"{HP}run/{HP}tbl") or ps[i - 1].findall(
                f"{HP}run/{HP}pic"
            ):
                continue
            host, nxt = int(ls[0].get("vertpos")), int(nx[0].get("vertpos"))
            prev_end = (
                int(pv[-1].get("vertpos"))
                + int(pv[-1].get("vertsize"))
                + int(pv[-1].get("spacing"))
            )
            if not (prev_end <= host < nxt):
                continue  # 쪽이 바뀜
            om = tb.find(f"{HP}outMargin")
            T = (
                int(pos.get("vertOffset"))
                + int(om.get("top"))
                + int(om.get("bottom"))
                + int(tb.find(f"{HP}sz").get("height"))
            )
            L = int(ls[0].get("vertsize")) + int(ls[0].get("spacing"))
            _, prev_sa = spacing(h, ps[i - 1].get("paraPrIDRef"))
            host_sb, host_sa = spacing(h, p.get("paraPrIDRef"))
            nxt_sb, _ = spacing(h, ps[i + 1].get("paraPrIDRef"))
            A, B = host - prev_end, nxt - host
            rows.append(
                (
                    Path(f).stem,
                    name[-12:],
                    i,
                    A,
                    B,
                    T,
                    L,
                    prev_sa,
                    host_sb,
                    host_sa,
                    nxt_sb,
                    int(pos.get("vertOffset")),
                    (
                        pos.get("flowWithText"),
                        pos.get("allowOverlap"),
                        pos.get("holdAnchorAndSO"),
                        pos.get("vertAlign"),
                        tb.get("pageBreak"),
                        p.get("pageBreak"),
                        tb.find(f"{HP}sz").get("heightRelTo"),
                        ls[0].get("horzsize") == "0",
                    ),
                    (int(tb.find(f"{HP}sz").get("width")), int(tb.find(f"{HP}sz").get("height")), int(ls[0].get("horzsize")), ls[0].get("flags")),
                )
            )

print("표본", len(rows))
kind = collections.Counter()
attr_by = collections.defaultdict(collections.Counter)
for r in rows:
    _, _, _, A, B, T, L, psa, hsb, hsa, nsb, off, attrs, dims = r
    if abs(A - T - psa - hsb) <= 2 and abs(B - L - hsa - nsb) <= 2:
        k = "아래(간격 모두 더함)"
    elif abs(A - T) <= 2 + psa + hsb and abs(B - L) <= 2 + hsa + nsb:
        k = "아래(간격 일부)"
    elif abs(A - psa - hsb) <= 2 and abs(B - T) <= 2 + hsa + nsb:
        k = "위"
    else:
        k = "기타"
    kind[k] += 1
    attr_by[k][attrs] += 1
    r += (k,)
    if k == "기타" and kind[k] <= 12:
        print("  기타", r)
for k, n in kind.most_common():
    print(k, n)
for k, c in attr_by.items():
    print(k, c.most_common(6))
samp = [r for r in rows if abs(r[3] - r[5]) <= 2 + r[7] + r[8]][:5]
print("아래 예", samp)
