"""정답본에서 「쪽 나눔(pageBreak=1) 문단 바로 앞 빈 문단」을 모아 한/글이 어디 두었는지 센다.

    python harvest_emptybreak.py

분류(빈 문단 첫 줄 vertpos 와 앞 문단 끝, 본문 높이로):
  새쪽 = vertpos 가 앞 문단 끝보다 작다(다음 쪽 첫머리로 넘어감 → 다음 문단의 쪽 나눔으로 빈 쪽이 생김)
  넘침 = 앞 쪽에 이어지되 줄 아래가 본문 높이를 넘는다(쪽 아래 여백으로 흡수)
  들어감 = 앞 쪽에 이어지고 본문 안
본문 높이는 구역 첫 pagePr 높이 - 위아래 여백 - 머리말/꼬리말(HWPUNIT).
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
    pp = re.search(r'<hp:pagePr [^>]*height="(\d+)"', x)
    mg = re.search(
        r'<hp:margin header="(\d+)" footer="(\d+)" gutter="\d+" left="\d+" right="\d+" top="(\d+)" bottom="(\d+)"',
        x,
    )
    if not pp or not mg:
        continue
    head, foot, top, bottom = (int(v) for v in mg.groups())
    body_h = int(pp.group(1)) - top - bottom - head - foot
    paras = body_xml(path)
    for i in range(1, len(paras) - 1):
        p, nxt, prev = paras[i], paras[i + 1], paras[i - 1]
        if not re.match(r'<hp:p\b[^>]*\bpageBreak="1"', nxt):
            continue
        body = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", p, flags=re.S)
        if re.search(r"<hp:t>[^<]", body) or re.search(
            r"<hp:(tbl|pic|rect|equation|container|ctrl)\b", body
        ):
            continue
        seg = re.search(
            r'<hp:lineseg textpos="\d+" vertpos="(-?\d+)" vertsize="(\d+)" textheight="\d+" baseline="\d+" spacing="(-?\d+)"',
            p,
        )
        psegs = re.findall(
            r'<hp:lineseg textpos="\d+" vertpos="(-?\d+)" vertsize="(\d+)" textheight="\d+" baseline="\d+" spacing="(-?\d+)"',
            prev,
        )
        if not seg or not psegs:
            continue
        v, lh, ls = (int(t) for t in seg.groups())
        pv, plh, pls = (int(t) for t in psegs[-1])
        prev_has_tbl = "<hp:tbl" in prev
        if v < pv:
            kind = "새쪽"
        elif v + lh > body_h:
            kind = "넘침"
        else:
            kind = "들어감"
        key = (kind, "앞에 표" if prev_has_tbl else "앞에 글")
        stat[key] += 1
        if len(ex[key]) < 6:
            ex[key].append(f"{doc} p{i} v={v} lh={lh} 앞끝={pv + plh} 본문={body_h}")
for k, n in sorted(stat.items()):
    print(n, k, ex[k][:3])
