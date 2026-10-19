"""새 정답본 문서 한 쪽의 글줄 기준선을 엔진(줄 배치 지운 사본, SVG)과 한/글(PDF)로 위에서부터 나란히 찍는다.

    python exp/ydiff.py <문서 이름> <쪽(0부터)> [줄 수]

열쇠(빈칸 뺀 앞 6글자)가 쪽 안에 한 번만 나오는 줄만 짝짓고, 차(px, 엔진 − 한/글)를 붙인다.
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
OUT = Path(__file__).resolve().parent.parent.parent / "out"
EXE = Path.home() / ".claude/skills/hwpx/editor/.build/rhwp/target/debug/rhwp.exe"
name, page = sys.argv[1], int(sys.argv[2])
limit = int(sys.argv[3]) if len(sys.argv) > 3 else 40
env = dict(os.environ, CLAUDE_METRICS_DIR=str(OUT / "metrics"))
with tempfile.TemporaryDirectory() as td:
    subprocess.run(
        [
            str(EXE),
            "export-svg",
            str(OUT / "fresh" / "in" / f"{name}.hwpx"),
            "-p",
            str(page),
            "-o",
            td,
        ],
        env=env,
        capture_output=True,
    )
    svg = next(Path(td).glob("*.svg")).read_text(encoding="utf-8")
lines = {}
for m in re.finditer(r"<text([^>]*)>([^<]*)</text>", svg):
    if 'fill-opacity="0"' in m.group(1):
        continue
    xy = text_xy(m.group(1))
    if xy:
        lines.setdefault(round(xy[1], 1), []).append((xy[0], m.group(2)))
eng = {}
for y, v in lines.items():
    k = "".join(c for _, c in sorted(v)).replace(" ", "")[:6]
    eng.setdefault(k, []).append(y)
han = {}
p = fitz.open(OUT / "fresh" / "rt" / f"{name}.pdf")[page]
for b in p.get_text("dict")["blocks"]:
    for ln in b.get("lines", []):
        t = "".join(s["text"] for s in ln["spans"]).replace(" ", "")[:6]
        if t:
            han.setdefault(t, []).append(
                round(ln["spans"][0]["origin"][1] * 96 / 72, 1)
            )
rows = sorted(
    (han[k][0], eng[k][0], k)
    for k in han
    if len(han[k]) == 1 and len(eng.get(k, [])) == 1
)
for h, e, k in rows[:limit]:
    print(f"{h:7.1f} {e:7.1f} {e - h:+6.1f}  {k}")
