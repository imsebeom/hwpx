"""make_bulletindent.py 변형을 rhwp(claude-linestarts CLAUDE_SVG)로 그려, 글머리 문단의 글머리, 첫 줄 「I」, 둘째 줄 첫 글자 x(pt)를 잰다.

python exp/read_bulletindent_svg.py <변형 폴더>
"""

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
src = Path(sys.argv[1])
EXE = (
    Path.home()
    / ".claude/skills/hwpx/editor/.build/rhwp/target/debug/claude-linestarts.exe"
)
PX2PT = 72 / 96


def glyphs(svg):
    out = []
    for a, t in re.findall(r"<text\b([^>]*)>([^<]*)</text>", svg):
        tr = re.search(r"translate\(([-\d.]+),([-\d.]+)\)", a)
        if tr:
            x, y = float(tr.group(1)), float(tr.group(2))
        else:
            mx, my = re.search(r'\bx="([-\d.]+)"', a), re.search(r'\by="([-\d.]+)"', a)
            if not (mx and my):
                continue
            x, y = float(mx.group(1)), float(my.group(1))
        if t.strip():
            out.append((y, x, t))
    return out


for f in sorted(src.glob("*.hwpx")):
    with tempfile.TemporaryDirectory() as d:
        env = dict(os.environ, CLAUDE_SVG=d)
        subprocess.run([str(EXE), str(f)], capture_output=True, env=env)
        svg = Path(d, "0.svg").read_text(encoding="utf-8")
    g = glyphs(svg)
    rows = {}
    for y, x, t in g:
        rows.setdefault(round(y, 1), []).append((x, t))
    ys = sorted(rows)
    res = None
    for i, y in enumerate(ys):
        line = sorted(rows[y])
        txt = "".join(t for _, t in line)
        if "IB전문성보유" in txt.replace(" ", ""):
            bullet = line[0][0]
            ib = next(x for x, t in line if t.startswith("I"))
            nxt = sorted(rows[ys[i + 1]])[0][0]
            res = (bullet * PX2PT, ib * PX2PT, nxt * PX2PT)
            break
    print(f.stem, " ".join(f"{v:7.2f}" for v in res) if res else "없음")
