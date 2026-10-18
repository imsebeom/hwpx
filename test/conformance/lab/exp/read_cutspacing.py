"""make_cutspacing.py 변형을 한/글이 다시 저장한 파일에서 둘째 표 행 2 칸마다 1쪽에 담은 줄 수(vpos 되감김 앞 줄 수)를 읽는다.

python read_cutspacing.py
"""

import glob
import os
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
base = os.path.join(os.environ["TEMP"], "cutsp")
for f in sorted(glob.glob(os.path.join(base, "rt", "o*.hwpx"))):
    s = zipfile.ZipFile(f).read("Contents/section0.xml").decode("utf-8")
    i = s.find('id="1748696691"')
    t = s[i : s.find("</hp:tbl>", i)]
    host = re.search(
        r'<hp:lineseg textpos="0" vertpos="(\d+)"', s[s.find("</hp:tbl>", i) :]
    )
    row = []
    for tc in re.findall(r"<hp:tc\b.*?</hp:tc>", t, re.S):
        col, r = re.search(r'colAddr="(\d+)" rowAddr="(\d+)"', tc).groups()
        if r != "2":
            continue
        vps = [
            int(v) for v in re.findall(r'<hp:lineseg textpos="\d+" vertpos="(\d+)"', tc)
        ]
        n = next((k for k in range(1, len(vps)) if vps[k] < vps[k - 1]), len(vps))
        row.append(f"c{col}:{n}/{len(vps)}")
    sz = re.findall(r'<hp:cellSz width="\d+" height="(\d+)"', t)[:6]
    print(
        os.path.basename(f),
        "host",
        host.group(1) if host else "-",
        " ".join(row),
        "rows01",
        sz[1],
        sz[4],
    )
