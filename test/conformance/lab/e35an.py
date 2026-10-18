"""e35 읽기: 오른쪽 여백(남는 폭)과 빈칸 묶음 길이별로 한/글과 rhwp 가 「가」 43자 뒤 앞줄에 남긴 빈칸 수.

python e35an.py
"""

import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
from nativescore import EXE  # noqa: E402

OUT = Path("../out/lab")
meta = json.load(open("e35_meta.json", encoding="utf-8"))


def han(name):
    x = (
        zipfile.ZipFile(OUT / "e35_rt" / f"{name}.hwpx")
        .read("Contents/section0.xml")
        .decode()
    )
    return [
        [int(v) for v in re.findall(r'<hp:lineseg textpos="(\d+)"', p)]
        for p in re.findall(r"<hp:p\b.*?</hp:p>", x, re.S)
        if "가가" in p
    ]


def rhwp(name):
    r = subprocess.run(
        [str(EXE), str(OUT / "e35" / f"{name}.hwpx")],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    rows = [
        json.loads(f[2])
        for f in (ln.split("\t") for ln in r.stdout.splitlines())
        if len(f) == 3 and f[1].isdigit()
    ]
    return rows[-4:]


cache = {}
for name, idx, right, k in meta:
    if name not in cache:
        cache[name] = (han(name), rhwp(name))
    a, b = cache[name][0][idx], cache[name][1][idx]
    keep = lambda st: (st[1] - 43) if len(st) > 1 else None  # noqa: E731
    print(
        f"여백 {right:3d} 빈칸{k}  한/글 {a} 남김 {keep(a)}  rhwp {b} 남김 {keep(b)}{'' if a == b else '  <- 다름'}"
    )
