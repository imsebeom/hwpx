"""임의의 HWPX 묶음을 엔진(SVG)과 한/글 PDF 로 견줘 문서마다 2pt 넘게 다른 글줄 수를 센다(저장 줄 배치 그대로 그린다).

    python exp/ydiff_any.py <입력 폴더> <PDF 폴더> [rhwp.exe]

rendery.py 와 같은 방식: 쪽마다 빈칸 뺀 앞 6글자 열쇠가 쪽 안에 한 번만 나오는 줄만 짝짓는다. 쪽수가 다르면 그 문서는 건너뛴다.
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
src, pdfs = Path(sys.argv[1]), Path(sys.argv[2])
exe = (
    sys.argv[3]
    if len(sys.argv) > 3
    else str(
        Path.home() / ".claude/skills/hwpx/editor/.build/rhwp/target/debug/rhwp.exe"
    )
)
env = dict(os.environ, CLAUDE_METRICS_DIR=str(OUT / "metrics"))


def keyed(pairs):
    d = {}
    for y, t in pairs:
        k = t.replace(" ", "")[:6]
        if k:
            d.setdefault(k, []).append(y)
    return {k: v[0] for k, v in d.items() if len(v) == 1}


total = bad_total = 0
for f in sorted(src.glob("*.hwpx")):
    pdf = pdfs / (f.stem + ".pdf")
    if not pdf.exists():
        continue
    doc = fitz.open(pdf)
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(
            [exe, "export-svg", str(f), "-o", td], env=env, capture_output=True
        )
        svgs = sorted(Path(td).glob("*.svg"))
        if len(svgs) != len(doc):
            print(f.stem, "쪽수 다름", len(doc), len(svgs))
            continue
        n = bad = 0
        worst = []
        for pi, svgp in enumerate(svgs):
            svg = svgp.read_text(encoding="utf-8")
            lines = {}
            for m in re.finditer(r"<text([^>]*)>([^<]*)</text>", svg):
                if 'fill-opacity="0"' in m.group(1):
                    continue
                xy = text_xy(m.group(1))
                if xy:
                    lines.setdefault(round(xy[1], 1), []).append((xy[0], m.group(2)))
            eng = keyed((y, "".join(c for _, c in sorted(v))) for y, v in lines.items())
            han = keyed(
                (
                    ln["spans"][0]["origin"][1] * 96 / 72,
                    "".join(s["text"] for s in ln["spans"]),
                )
                for b in doc[pi].get_text("dict")["blocks"]
                for ln in b.get("lines", [])
            )
            for k in han.keys() & eng.keys():
                d = (eng[k] - han[k]) * 0.75
                n += 1
                if abs(d) > 2:
                    bad += 1
                    worst.append((pi + 1, k, round(d, 1)))
    total += n
    bad_total += bad
    print(f.stem, "줄", n, "2pt 넘음", bad, worst[:4])
print("합", bad_total, "/", total)
