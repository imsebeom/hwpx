"""정답본에서 단 나누기(columnBreak=1) 문단을 모아 한/글이 새 쪽(단)에서 시작했는지 센다(1단 구역만).

    python harvest_colbreak.py

새쪽 = 첫 줄 vertpos 가 앞 문단 마지막 줄보다 작다. 이어짐 = 크거나 같다.
빈 문단인지, 다음 문단이 쪽 나눔인지, 앞 문단이 표인지로 나눠 센다.
"""

import collections
import glob
import os
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
from pagediff import body_xml  # noqa: E402

stat = collections.Counter()
ex = collections.defaultdict(list)
for path in sorted(glob.glob("../out/oracle/*.hwpx")):
    doc = os.path.basename(path)[:-5]
    x = zipfile.ZipFile(path).read("Contents/section0.xml").decode("utf-8", "replace")
    cols = re.findall(r'<hp:colPr [^>]*colCount="(\d+)"', x)
    if any(c != "1" for c in cols):
        continue
    paras = body_xml(path)
    for i in range(1, len(paras)):
        p = paras[i]
        if not re.match(r'<hp:p\b[^>]*\bcolumnBreak="1"', p):
            continue
        seg = re.search(r'<hp:lineseg textpos="\d+" vertpos="(-?\d+)"', p)
        pv = re.findall(r'<hp:lineseg textpos="\d+" vertpos="(-?\d+)"', paras[i - 1])
        if not seg or not pv:
            continue
        body = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", p, flags=re.S)
        empty = not re.search(r"<hp:t>[^<]", body) and not re.search(
            r"<hp:(tbl|pic|rect|container)\b", body
        )
        nxt_pb = (
            i + 1 < len(paras)
            and re.match(r'<hp:p\b[^>]*\bpageBreak="1"', paras[i + 1]) is not None
        )
        kind = "새쪽" if int(seg.group(1)) < int(pv[-1]) else "이어짐"
        key = (
            kind,
            "빈 문단" if empty else "글 문단",
            "다음 쪽나눔" if nxt_pb else "-",
            "앞 표" if "<hp:tbl" in paras[i - 1] else "앞 글",
        )
        stat[key] += 1
        if len(ex[key]) < 4:
            ex[key].append(f"{doc} p{i}")
for k, n in sorted(stat.items(), key=lambda kv: -kv[1]):
    print(n, k, ex[k])
