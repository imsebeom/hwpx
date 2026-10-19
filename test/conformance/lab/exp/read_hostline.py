"""make_hostline.py 변형을 엔진(SVG)과 한/글(PDF)로 견준다: 「가. 목적」 줄과 다음 문단 「다양한 체험」 줄의 기준선, 표 칸 글 「담당」.

python exp/read_hostline.py <rhwp.exe> <입력 폴더> <rt 폴더> <글꼴 폭 표 폴더>
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
KEYS = ("가.목적", "다양한체험", "담당")


def find(lines):
    out = {}
    for y, t in lines:
        t = t.replace(" ", "")
        for k in KEYS:
            if t.startswith(k) and k not in out:
                out[k] = round(y, 1)
    return out


for f in sorted(Path(src).glob("*.hwpx"), key=lambda p: int(p.stem[1:])):
    doc = fitz.open(Path(rt) / (f.stem + ".pdf"))
    pno = 4  # d034 p65 는 5쪽
    han = find(
        (ln["spans"][0]["origin"][1] * 96 / 72, "".join(s["text"] for s in ln["spans"]))
        for b in doc[pno].get_text("dict")["blocks"]
        for ln in b.get("lines", [])
    )
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(
            [exe, "export-svg", str(f), "-p", str(pno), "-o", td],
            env=env,
            capture_output=True,
        )
        svg = next(Path(td).glob("*.svg")).read_text(encoding="utf-8")
    rows = {}
    for m in re.finditer(r"<text([^>]*)>([^<]*)</text>", svg):
        xy = text_xy(m.group(1))
        if xy:
            rows.setdefault(round(xy[1], 1), []).append((xy[0], m.group(2)))
    eng = find((y, "".join(c for _, c in sorted(v))) for y, v in sorted(rows.items()))
    print(f.stem, " | ".join(f"{k} 한/글 {han.get(k)} 엔진 {eng.get(k)}" for k in KEYS))
