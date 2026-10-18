"""첫 run 에 구역/단 정의(secPr, colPr 등 보이지 않는 조판 부호)만 있고 그 글자 크기(A)가 뒤 run 크기(B)와 다른 본문 문단에서,
한/글 첫 줄 높이(vertsize)와 줄 간격(spacing)이 A, B 중 무엇을 따르는지 센다.

    python harvest_secprrun.py
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
    z = zipfile.ZipFile(path)
    h = z.read("Contents/header.xml").decode("utf-8", "replace")
    size = dict(re.findall(r'<hh:charPr id="(\d+)" height="(\d+)"', h))
    pls = {}
    for m in re.finditer(r'<hh:paraPr id="(\d+)".*?</hh:paraPr>', h, re.S):
        ls = re.search(r'<hh:lineSpacing type="(\w+)" value="(-?\d+)"', m.group(0))
        pls[m.group(1)] = (ls.group(1), int(ls.group(2))) if ls else None
    for p in body_xml(path)[:3]:
        segs = re.findall(
            r'<hp:lineseg textpos="\d+" vertpos="-?\d+" vertsize="(\d+)" textheight="\d+" baseline="\d+" spacing="(-?\d+)"',
            p,
        )
        if not segs:
            continue
        top = re.sub(
            r"<hp:subList\b.*?</hp:subList>",
            "",
            re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", p, flags=re.S),
            flags=re.S,
        )
        runs = re.findall(r'<hp:run charPrIDRef="(\d+)">(.*?)</hp:run>', top, re.S)
        if (
            len(runs) < 2
            or "<hp:secPr" not in runs[0][1]
            or re.search(r"<hp:t>[^<]", runs[0][1])
            or "<hp:tbl" in runs[0][1]
        ):
            continue
        a = int(size.get(runs[0][0], 0))
        b = max(int(size.get(c, 0)) for c, _ in runs[1:])
        if a == b:
            continue
        ls = pls.get(re.search(r'paraPrIDRef="(\d+)"', p).group(1))
        vs, sp = int(segs[0][0]), int(segs[0][1])
        has_obj = bool(
            re.search(
                r"<hp:(tbl|pic|equation|container|rect)\b",
                "".join(r[1] for r in runs[1:]),
            )
        )
        want = {"A": a, "B": b}
        if ls and ls[0] == "PERCENT":
            fit = [k for k, f in want.items() if abs(sp - f * (ls[1] - 100) / 100) <= 2]
            key = (
                "간격이 " + ("/".join(fit) if fit else "둘 다 아님"),
                "개체줄" if has_obj else "글줄",
            )
        else:
            key = ("비율 간격 아님", "개체줄" if has_obj else "글줄")
        stat[key] += 1
        if len(ex[key]) < 4:
            ex[key].append(f"{doc} A={a} B={b} vs={vs} sp={sp} {ls}")
for k, n in sorted(stat.items(), key=lambda kv: -kv[1]):
    print(n, k, ex[k])
