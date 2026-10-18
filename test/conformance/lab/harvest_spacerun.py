"""정답본 전체에서 줄이 빈칸 묶음(2개 이상) 가운데서 꺾인 자리마다 한/글이 앞줄에 남긴 빈칸 수와 묶음 길이, 정렬을 센다.

    python harvest_spacerun.py

한/글 줄 시작은 정답본(한/글 저장) linesegarray 의 textpos. 본문과 칸 문단 모두.
"""

import collections
import glob
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
from showmm import stream  # noqa: E402

stat = collections.Counter()
examples = collections.defaultdict(list)
for path in sorted(glob.glob("../out/oracle/*.hwpx")):
    z = zipfile.ZipFile(path)
    h = z.read("Contents/header.xml").decode()
    aligns = {
        m.group(1): re.search(r'<hh:align horizontal="(\w+)"', m.group(0)).group(1)
        for m in re.finditer(r'<hh:paraPr id="(\d+)".*?</hh:paraPr>', h, re.S)
    }
    for n in sorted(
        x for x in z.namelist() if re.match(r"Contents/section\d+\.xml$", x)
    ):
        x = z.read(n).decode()
        for m in re.finditer(r"<hp:p\b[^>]*>(?:(?!<hp:p\b).)*?</hp:p>", x, re.S):
            p = m.group(0)
            starts = [int(v) for v in re.findall(r'<hp:lineseg textpos="(\d+)"', p)]
            if len(starts) < 2 or "  " not in p:
                continue
            s = stream(p)
            al = aligns.get(re.search(r'paraPrIDRef="(\d+)"', p).group(1), "?")
            for st in starts[1:]:
                if st <= 0 or st > len(s) or s[st - 1] != " ":
                    continue
                i = st
                while i > 0 and s[i - 1] == " ":
                    i -= 1
                j = st
                while j < len(s) and s[j] == " ":
                    j += 1
                run = j - i
                if run < 2 or j == len(s):
                    continue
                kept = st - i
                key = (al, min(run, 9), kept)
                stat[key] += 1
                if len(examples[key]) < 2:
                    examples[key].append(path.split("\\")[-1].split("/")[-1])
for al in sorted({k[0] for k in stat}):
    print(f"== {al}")
    for run in range(2, 10):
        row = {k[2]: v for k, v in stat.items() if k[0] == al and k[1] == run}
        if row:
            print(
                f"  묶음 {run}{'+' if run == 9 else ' '}  남김별 "
                + "  ".join(f"{kept}:{v}" for kept, v in sorted(row.items()))
            )
