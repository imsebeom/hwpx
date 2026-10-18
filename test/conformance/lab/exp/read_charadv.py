"""make_charadv.py 변형의 글자 전진 폭(16글자 평균, pt)을 한/글 PDF 와 엔진(CLAUDE_XP 커서 x)으로 나란히 찍는다.

python exp/read_charadv.py <폴더: in/*.hwpx, rt/*.pdf>
"""

import os
import subprocess
import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8")
base = Path(sys.argv[1])
EXE = (
    Path.home()
    / ".claude/skills/hwpx/editor/.build/rhwp/target/debug/claude-linestarts.exe"
)


def han(pdf):
    for pg in fitz.open(pdf):
        for b in pg.get_text("rawdict")["blocks"]:
            for ln in b.get("lines", []):
                cs = [c for s in ln["spans"] for c in s["chars"]]
                t = "".join(c["c"] for c in cs)
                i, j = t.find("QZ"), t.find("ZQ")
                if i >= 0 and j > i:
                    x = [c["origin"][0] for c in cs]
                    a = i + 2
                    return (x[a + 16] - x[a]) / 16, (x[j] - x[a + 16]) / 16, j - a
    return None


def eng(hwpx):
    r = subprocess.run(
        [str(EXE), str(hwpx)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "CLAUDE_XP": "121"},
    )
    x = {}
    for line in r.stdout.splitlines():
        f = line.split("\t")
        if len(f) >= 4 and f[1] == "XP" and f[2].startswith("1:121:"):
            x[int(f[2].split(":")[2])] = float(f[3].split(":")[0])
    if 34 not in x:
        return None
    return (x[18] - x[2]) / 16, (x[34] - x[18]) / 16


print("글자        한/글(자간0, -2%)    엔진(자간0, -2%)")
for f in sorted((base / "in").glob("c_*.hwpx")):
    h = han(base / "rt" / (f.stem + ".pdf"))
    e = eng(f)
    hs = f"{h[0]:7.3f} {h[1]:7.3f}" if h else "   -   "
    es = f"{e[0]:7.3f} {e[1]:7.3f}" if e else "   -   "
    print(f"{f.stem[2:]:10s} {hs}      {es}")
