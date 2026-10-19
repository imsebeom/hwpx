"""그리기 위치 지표: 줄 배치를 지운 사본(out/fresh/in)을 네이티브 엔진이 그린 SVG 와 한/글 새 조판 PDF(out/fresh/rt)의 글줄 기준선 y 를 견준다.

    python exp/rendery.py [--ids d001,d002] [--show 5] [--stored]

--stored 면 한/글이 저장한 줄 배치가 있는 out/fresh/rt 를 그린다(한/글로 연 문서를 그대로 보여 줄 때).

쪽수가 같은 문서만, 쪽마다 글줄을 앞 6글자(빈칸 뺌)로 짝짓고(쪽 안에서 한 번만 나오는 열쇠만) 기준선 차(pt)를 센다.
엔진 SVG 의 text y 는 px(0.75 를 곱해 pt), PDF 는 pt. 조판(쪽 나눔)이 아니라 그리기(layout)가 한/글과 얼마나 같은지 본다.
"""

import concurrent.futures as cf
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import fitz
from svgpos import text_xy

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent.parent
OUT = HERE.parent / "out"
EXE = (
    Path.home()
    / ".claude/skills/hwpx/editor/.build/rhwp/target/debug/claude-linestarts.exe"
)
args = sys.argv[1:]
ids = set(args[args.index("--ids") + 1].split(",")) if "--ids" in args else None
show = int(args[args.index("--show") + 1]) if "--show" in args else 0
stored = "--stored" in args


def lines_from_chars(chars):
    rows = {}
    for x, y, c in chars:
        rows.setdefault(round(y, 1), []).append((x, c))
    out = []
    for y, cs in rows.items():
        t = re.sub(r"\s", "", "".join(c for _, c in sorted(cs)))
        if len(t) >= 6:
            out.append((t[:6], y))
    return out


def keyed(lines):
    cnt = Counter(k for k, _ in lines)
    return {k: y for k, y in lines if cnt[k] == 1}


def one(name):
    src = OUT / "fresh" / ("rt" if stored else "in") / f"{name}.hwpx"
    pdf = OUT / "fresh" / "rt" / f"{name}.pdf"
    if not pdf.exists():
        return name, "PDF 없음"
    d = tempfile.mkdtemp(prefix="rendery_")
    subprocess.run(
        [str(EXE), str(src)],
        capture_output=True,
        env={
            **os.environ,
            "CLAUDE_SVG": d,
            "CLAUDE_METRICS_DIR": str(OUT / "metrics"),
        },
    )
    svgs = sorted(Path(d).glob("*.svg"), key=lambda p: int(p.stem))
    doc = fitz.open(pdf)
    if len(svgs) != len(doc):
        return name, None
    res = []
    for i, (sv, pg) in enumerate(zip(svgs, doc)):
        s = sv.read_text(encoding="utf-8")
        ech = []
        for m in re.finditer(r"<text\b([^>]*)>([^<]*)</text>", s):
            xy = text_xy(m.group(1))
            if xy:
                ech.append((xy[0] * 0.75, xy[1] * 0.75, m.group(2)))
        hch = [
            (c["origin"][0], c["origin"][1], c["c"])
            for b in pg.get_text("rawdict")["blocks"]
            for ln in b.get("lines", [])
            for sp in ln["spans"]
            for c in sp["chars"]
        ]
        e, h = keyed(lines_from_chars(ech)), keyed(lines_from_chars(hch))
        for k in e.keys() & h.keys():
            res.append((i + 1, k, round(e[k] - h[k], 1)))
    return name, res


files = sorted(p.stem for p in (OUT / "fresh" / "in").glob("*.hwpx"))
if ids:
    files = [f for f in files if f in ids]
tot = Counter()
hist = Counter()
worst = []
with cf.ThreadPoolExecutor(8) as ex:
    for name, res in ex.map(one, files):
        if res is None or isinstance(res, str):
            tot["PDF 없음" if res else "쪽수 다름"] += 1
            continue
        tot["문서"] += 1
        tot["줄"] += len(res)
        hist.update(round(r[2]) for r in res)
        bad = [r for r in res if abs(r[2]) > 2.0]
        tot["2pt 넘게 다름"] += len(bad)
        if bad:
            worst.append((len(bad), name, bad[:show] if show else bad[:1]))
print(dict(tot))
print("차 분포(pt, 반올림):", sorted(hist.items(), key=lambda kv: -kv[1])[:15])
for n, name, ex_ in sorted(worst, reverse=True)[:25]:
    print(f"{name} {n}줄", ex_)
