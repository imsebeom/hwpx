"""정답본의 글머리 줄(첫 글자가 기호인 줄)마다 둘째 글자 x 를 한/글 PDF 와 rhwp(claude-linestarts CLAUDE_SVG)로 견준다.

    python exp/bulletx.py <정답본 id> ...      (한/글 PDF: ../out/lab/hanpdf/rt/<id>.pdf)

줄은 글머리 뒤 앞 8글자(빈칸 뺌)로 짝짓는다. 차이(pt) 분포를 찍는다.
"""

import os
import re
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8")
EXE = (
    Path.home()
    / ".claude/skills/hwpx/editor/.build/rhwp/target/debug/claude-linestarts.exe"
)
OUT = Path(__file__).resolve().parent.parent.parent / "out"


def is_mark(ch):
    return unicodedata.category(ch)[0] in "SP" and ch not in "([{<\"'"


def han_lines(pdf):
    res = {}
    for pno, pg in enumerate(fitz.open(pdf)):
        for b in pg.get_text("rawdict")["blocks"]:
            for ln in b.get("lines", []):
                ch = [c for sp in ln["spans"] for c in sp["chars"] if c["c"].strip()]
                if len(ch) > 3 and is_mark(ch[0]["c"]):
                    key = (pno, "".join(c["c"] for c in ch[1:9]))
                    res[key] = ch[1]["origin"][0] - ch[0]["origin"][0]
    return res


def rh_lines(hwpx):
    res = {}
    with tempfile.TemporaryDirectory() as d:
        stripped = Path(d) / "s.hwpx"
        src = zipfile.ZipFile(hwpx)
        with zipfile.ZipFile(stripped, "w", zipfile.ZIP_DEFLATED) as z:
            for it in src.infolist():
                data = src.read(it.filename)
                if re.match(r"Contents/section\d+\.xml", it.filename):
                    data = re.sub(
                        rb"<hp:linesegarray>.*?</hp:linesegarray>",
                        b"",
                        data,
                        flags=re.S,
                    )
                z.writestr(
                    zipfile.ZipInfo(it.filename), data, compress_type=it.compress_type
                )
        env = dict(os.environ, CLAUDE_SVG=d)
        subprocess.run([str(EXE), str(stripped)], capture_output=True, env=env)
        for svgf in Path(d).glob("*.svg"):
            pno = int(svgf.stem)
            rows = {}
            for a, t in re.findall(
                r"<text\b([^>]*)>([^<]*)</text>", svgf.read_text(encoding="utf-8")
            ):
                tr = re.search(r"translate\(([-\d.]+),([-\d.]+)\)", a)
                if tr:
                    x, y = float(tr.group(1)), float(tr.group(2))
                else:
                    mx, my = (
                        re.search(r'\bx="([-\d.]+)"', a),
                        re.search(r'\by="([-\d.]+)"', a),
                    )
                    if not (mx and my):
                        continue
                    x, y = float(mx.group(1)), float(my.group(1))
                for k, c in enumerate(t):
                    if c.strip():
                        rows.setdefault(round(y), []).append((x + k * 0.01, c))
            for y, items in rows.items():
                items.sort()
                if len(items) > 3 and is_mark(items[0][1]):
                    key = (pno, "".join(c for _, c in items[1:9]))
                    res[key] = (items[1][0] - items[0][0]) * 0.75
    return res


for did in sys.argv[1:]:
    h = han_lines(OUT / "lab" / "hanpdf" / "rt" / f"{did}.pdf")
    r = rh_lines(OUT / "oracle" / f"{did}.hwpx")
    common = [k for k in h if k in r]
    diffs = [r[k] - h[k] for k in common]
    within = sum(1 for d in diffs if abs(d) <= 1.0)
    print(
        f"{did} 글머리 줄 한/글 {len(h)} rhwp {len(r)} 짝 {len(common)} | 1pt 안 {within}",
        end="",
    )
    if diffs:
        print(
            f" | 평균 차 {sum(diffs) / len(diffs):+.2f}pt 최대 {max(diffs, key=abs):+.2f}"
        )
    else:
        print()
