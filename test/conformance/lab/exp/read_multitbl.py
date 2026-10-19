"""make_multitbl.py 변형을 엔진(SVG)과 한/글(PDF)로 견준다: 표 가로선 y 와 표 뒤 첫 글줄 「긴 표」 기준선.

python exp/read_multitbl.py <rhwp.exe> <입력 폴더> <rt 폴더> <글꼴 폭 표 폴더>
"""

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
from svgpos import text_xy  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
exe, src, rt, metrics = sys.argv[1:5]
env = dict(os.environ, CLAUDE_METRICS_DIR=metrics)
for f in sorted(Path(src).glob("*.hwpx")):
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(
            [exe, "export-svg", str(f), "-p", "0", "-o", td],
            env=env,
            capture_output=True,
        )
        svg = next(Path(td).glob("*.svg")).read_text(encoding="utf-8")
    lines = {}
    for m in re.finditer(r"<text([^>]*)>([^<]*)</text>", svg):
        xy = text_xy(m.group(1))
        if xy:
            lines.setdefault(round(xy[1], 1), []).append((xy[0], m.group(2)))
    eng = sorted(
        y for y, v in lines.items() if "".join(c for _, c in sorted(v)).startswith("긴")
    )
    ehl = sorted(
        {
            round(float(m.group(2)), 1)
            for m in re.finditer(
                r'<line x1="([\d.]+)" y1="([\d.]+)" x2="([\d.]+)" y2="\2"', svg
            )
            if abs(float(m.group(3)) - float(m.group(1))) > 200
        }
    )
    p = fitz.open(Path(rt) / (f.stem + ".pdf"))[0]
    han = [
        round(ln["spans"][0]["origin"][1] * 96 / 72, 1)
        for b in p.get_text("dict")["blocks"]
        for ln in b.get("lines", [])
        if "".join(s["text"] for s in ln["spans"]).strip().startswith("긴")
    ]
    hhl = sorted(
        {
            round(min(d["rect"].y0, d["rect"].y1) * 96 / 72, 1)
            for d in p.get_drawings()
            if d["rect"].height < 2 and d["rect"].width > 200
        }
    )
    print(f.stem, "긴 표: 엔진", eng, "한/글", han)
    print("   가로선 엔진", ehl[:7])
    print("   가로선 한/글", hhl[:7])
