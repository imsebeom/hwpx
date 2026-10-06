"""그림이 든 표 속 표의 높이, 그림 칸 높이, 그 칸 문단들의 vertpos 를 찍는다: python measure.py <hwpx...>"""

import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
for f in sys.argv[1:]:
    s = zipfile.ZipFile(f).read("Contents/section0.xml").decode()
    i = s.find("<hp:pic ")
    t = s.rfind("<hp:tbl ", 0, i)
    tsz = re.search(r'<hp:sz width="(\d+)"[^>]*height="(\d+)"', s[t:])
    psz = re.search(r'<hp:sz width="(\d+)" widthRelTo="ABSOLUTE" height="(\d+)"', s[i:])
    tc = s.rfind("<hp:tc ", 0, i)
    tc_end = s.find("</hp:tc>", i)
    cell = s[tc:tc_end]
    csz = re.search(r'<hp:cellSz width="(\d+)" height="(\d+)"', cell)
    paras = []
    for p in re.finditer(r"<hp:p\b[^>]*>(.*?)</hp:p>", cell, re.S):
        body = p.group(1)
        if "<hp:pic " in body or "fieldBegin" in body or "<hp:tbl " in body:
            # 그림 문단: 그 문단의 lineseg
            pass
        txt = "".join(
            re.findall(
                r"<hp:t\b[^>]*>([^<]*)</hp:t>",
                re.sub(r"<hp:subList.*?</hp:subList>", "", body, flags=re.S),
            )
        )[:18]
        segs = re.findall(
            r'<hp:lineseg textpos="\d+" vertpos="(\d+)" vertsize="(\d+)"', body
        )
        paras.append((txt, [(int(v), int(h)) for v, h in segs][:3]))
    print(
        f.rsplit("/", 1)[-1],
        "| 표 속 표 sz h",
        tsz.group(2),
        "| 그림 sz",
        psz.group(1),
        "x",
        psz.group(2),
        "| 그림 칸 cellSz h",
        csz.group(2),
    )
    for txt, segs in paras:
        print("    문단", repr(txt), segs)
