"""두 hwpx 의 최상위 문단과 표 행의 줄 배치(vertpos, 높이)를 나란히 찍는다. python segcmp.py a.hwpx b.hwpx"""

import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")


def top_paras(path):
    sec = zipfile.ZipFile(path).read("Contents/section0.xml").decode()
    out, depth, start = [], 0, None
    for m in re.finditer(r"<hp:p |</hp:p>|<hp:subList|</hp:subList>", sec):
        t = m.group(0)
        if t == "<hp:subList":
            depth += 1
        elif t == "</hp:subList>":
            depth -= 1
        elif t == "<hp:p " and depth == 0:
            start = m.start()
        elif t == "</hp:p>" and depth == 0 and start is not None:
            out.append(sec[start : m.end()])
            start = None
    return out


def summary(p):
    # 표 안 줄 배치는 빼고 최상위 문단 자신의 것만
    own = re.sub(r"<hp:subList.*?</hp:subList>", "", p, flags=re.S)
    segs = re.findall(
        r'<hp:lineseg textpos="(\d+)" vertpos="(-?\d+)" vertsize="(\d+)" textheight="\d+" baseline="\d+" spacing="(\d+)"',
        own,
    )
    tbl = re.search(
        r'<hp:tbl [^>]*>.*?<hp:sz width="(\d+)"[^>]*height="(\d+)"', p, re.S
    )
    txt = "".join(re.findall(r"<hp:t>([^<]*)", own))[:18]
    return segs, (tbl.group(2) if tbl else ""), txt


a, b = top_paras(sys.argv[1]), top_paras(sys.argv[2])
print(
    f"{'#':>2} {'한글 vpos/높이/간격':<34} {'rhwp vpos/높이/간격':<34} 표높이(한글/rhwp) 글"
)
for i in range(max(len(a), len(b))):
    sa = summary(a[i]) if i < len(a) else ([], "", "")
    sb = summary(b[i]) if i < len(b) else ([], "", "")
    fa = " ".join(f"{v}/{h}/{s}" for _, v, h, s in sa[0][:2])
    fb = " ".join(f"{v}/{h}/{s}" for _, v, h, s in sb[0][:2])
    print(f"{i:>2} {fa:<34} {fb:<34} {sa[1]}/{sb[1]} {sa[2]}")
