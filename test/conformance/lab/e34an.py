"""e34 읽기: 문단마다 둘째 줄 시작(textpos)을 한/글 재저장본과 rhwp(네이티브)로 나란히. 빈칸 묶음 가운데 앞줄에 남은 빈칸 수도.

python e34an.py
"""

import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
from nativescore import EXE  # noqa: E402

meta = json.load(open("e34_meta.json", encoding="utf-8"))
OUT = Path("../out/lab")


def han_starts(name):
    x = (
        zipfile.ZipFile(OUT / "e34_rt" / f"{name}.hwpx")
        .read("Contents/section0.xml")
        .decode()
    )
    paras = re.findall(r"<hp:p\b.*?</hp:p>", x, re.S)
    res = []
    for p in paras:
        if "가가" not in p:
            continue
        res.append([int(v) for v in re.findall(r'<hp:lineseg textpos="(\d+)"', p)])
    return res


def rhwp_starts(name):
    r = subprocess.run(
        [str(EXE), str(OUT / "e34" / f"{name}.hwpx")],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    res = []
    for line in r.stdout.splitlines():
        f = line.split("\t")
        if len(f) == 3 and f[1].isdigit():
            res.append(json.loads(f[2]))
    return res


cache = {}
for name, idx, align, n, k in meta:
    if name not in cache:
        cache[name] = (han_starts(name), rhwp_starts(name))
    han, rh = cache[name]
    a = han[idx]
    b = [s for s in rh if s][idx + (len(rh) - len(han))] if len(rh) >= len(han) else []
    keep = lambda st: (st[1] - n) if len(st) > 1 else None  # noqa: E731  앞줄에 남은 빈칸 수
    mark = "" if a == b else "  <- 다름"
    print(
        f"{align:7s} 가{n} 빈칸{k}  한/글 {a} 남김 {keep(a)}  rhwp {b} 남김 {keep(b)}{mark}"
    )
