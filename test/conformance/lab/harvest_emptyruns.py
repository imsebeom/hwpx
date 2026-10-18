"""글도 개체도 없는 문단(본문, 칸)에 크기가 다른 run 이 여럿이면 한/글 줄 높이(vertsize)가 어느 run 크기를 따르는지 센다.

    python harvest_emptyruns.py

후보: 첫 run, 마지막 run, 가장 큰 run. 구역 정의(secPr) 같은 조판 부호만 든 run 도 run 으로 친다.
"""

import collections
import glob
import os
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")

stat = collections.Counter()
ex = collections.defaultdict(list)
for path in sorted(glob.glob("../out/oracle/*.hwpx")):
    doc = os.path.basename(path)[:-5]
    z = zipfile.ZipFile(path)
    h = z.read("Contents/header.xml").decode("utf-8", "replace")
    size = dict(re.findall(r'<hh:charPr id="(\d+)" height="(\d+)"', h))
    for name in z.namelist():
        if not re.match(r"Contents/section\d+\.xml$", name):
            continue
        s = z.read(name).decode("utf-8")
        # 안에 다른 문단이 없는 문단만(칸 안 문단 포함)
        for p in re.findall(r"<hp:p [^>]*>(?:(?!<hp:p ).)*?</hp:p>", s, re.S):
            segs = re.findall(r'vertsize="(\d+)"', p)
            if len(segs) != 1:
                continue
            body = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", p, flags=re.S)
            if re.search(r"<hp:t>[^<]", body) or re.search(
                r"<hp:(tbl|pic|equation|container|rect|line|ellipse|ole|arc|polygon|curve|textart)\b",
                body,
            ):
                continue
            ids = re.findall(r'<hp:run charPrIDRef="(\d+)"', body)
            sizes = [int(size.get(i, 0)) for i in ids]
            if len(set(sizes)) < 2:
                continue
            vs = int(segs[0])
            fit = []
            if vs == sizes[0]:
                fit.append("첫")
            if vs == sizes[-1]:
                fit.append("끝")
            if vs == max(sizes):
                fit.append("최대")
            key = "/".join(fit) or "모두 아님"
            stat[key] += 1
            if len(ex[key]) < 5:
                ex[key].append(f"{doc} {sizes} vs={vs}")
for k, n in stat.most_common():
    print(n, k, ex[k])
