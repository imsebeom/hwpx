"""make_bulletindent.py 변형의 한/글 PDF(재저장 폴더)와 rhwp(claude-linestarts CLAUDE_XP)에서 글머리 문단의 글머리, 첫 줄, 둘째 줄 x 를 잰다.

    python exp/read_bulletindent.py <한/글 재저장 폴더> <변형 폴더>

x 는 단 왼쪽 기준 HWPUNIT(한/글 PDF 의 글머리 x 에서 들여쓰기만큼 되돌려 단 왼쪽을 잡는다).
"""

import os
import re
import subprocess
import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8")
rt, src = Path(sys.argv[1]), Path(sys.argv[2])
HU = 7200 / 72  # pt → HWPUNIT
EXE = (
    Path.home()
    / ".claude/skills/hwpx/editor/.build/rhwp/target/debug/claude-linestarts.exe"
)
COL_LEFT_PT = None


def han(pdf):
    pg = fitz.open(pdf)[0]
    lines = []
    for b in pg.get_text("rawdict")["blocks"]:
        for ln in b.get("lines", []):
            ch = [c for sp in ln["spans"] for c in sp["chars"] if c["c"].strip()]
            if ch:
                lines.append((ln["bbox"][1], ch))
    lines.sort(key=lambda r: r[0])
    for i, (_, ch) in enumerate(lines):
        t = "".join(c["c"] for c in ch)
        if "IB전문성보유" in t:
            first = ch[0]["origin"][0]
            text = next(c for c in ch if c["c"] == "I")["origin"][0]
            second = lines[i + 1][1][0]["origin"][0]
            return first, text, second
    return None


def rh(path):
    env = dict(os.environ, CLAUDE_XP="8")
    out = subprocess.run(
        [str(EXE), str(path)], capture_output=True, text=True, encoding="utf-8", env=env
    ).stdout
    xs = []
    for line in out.splitlines():
        m = re.search(r"\tXP\t0:8:(\d+)\t([-\d.]+):([-\d.]+)", line)
        if m:
            xs.append((int(m.group(1)), float(m.group(2)), float(m.group(3))))
    if not xs:
        return None
    y0 = xs[0][2]
    second = next((x for _, x, y in xs if y > y0 + 1), None)
    return xs[1][1], second  # 글자 1 = 「I」(글자 0 은 빈칸)


print(
    "변형        한/글: 글머리  첫줄I   둘째줄   | rhwp: 첫줄I  둘째줄   (pt, 쪽 왼쪽 기준)"
)
for pdf in sorted(rt.glob("*.pdf")):
    h = han(pdf)
    r = rh(src / f"{pdf.stem}.hwpx")
    hs = " ".join(f"{v:7.2f}" for v in h) if h else "없음"
    rs = (
        " ".join(f"{v:7.2f}" if v is not None else "  없음 " for v in r)
        if r
        else "없음"
    )
    print(f"{pdf.stem:12s} {hs} | {rs}")
