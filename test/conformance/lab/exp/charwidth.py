"""글자 폭 지표: 왼쪽 정렬 사본(exp/make_leftalign.py → out/left)을 한/글 PDF 와 네이티브 엔진 SVG 로 그려 글자 전진 폭을 견준다.

    python exp/charwidth.py [--ids d001,d002] [--top 40]

쪽마다 글줄을 앞 6글자(빈칸 뺌)로 짝짓고, 빈칸 뺀 글자열이 같은 줄만 쓴다. 이웃한 두 글자(사이에 빈칸 없음, 한/글 PDF 기준)의 x 차를
앞 글자의 전진 폭으로 보고 (글꼴, 크기, 글자)마다 엔진 − 한/글(pt) 평균을 낸다. 빈칸 폭은 빈칸을 낀 쌍에서 따로 센다.
양쪽 정렬을 없앴으므로 줄 안 간격은 자연 폭이다(빈칸 줄이기도 쓰이지 않는다).
"""

import atexit
import concurrent.futures as cf
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
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
top = int(args[args.index("--top") + 1]) if "--top" in args else 40
DEC = {"&lt;": "<", "&gt;": ">", "&quot;": '"', "&apos;": "'", "&amp;": "&"}


def dec(s):
    for k, v in DEC.items():
        s = s.replace(k, v)
    return s


def rows_of(chars):
    rows = defaultdict(list)
    for x, y, c, meta in chars:
        rows[round(y, 1)].append((x, c, meta))
    out = {}
    cnt = Counter()
    for y, cs in rows.items():
        cs.sort(key=lambda t: t[0])
        key = "".join(c for _, c, _ in cs if not c.isspace())[:6]
        if len(key) >= 6:
            cnt[key] += 1
            out[key] = cs
    return {k: v for k, v in out.items() if cnt[k] == 1}


def one(name):
    src = OUT / "left" / "in" / f"{name}.hwpx"
    pdf = OUT / "left" / "rt" / f"{name}.pdf"
    if not pdf.exists():
        return name, None
    d = tempfile.mkdtemp(prefix="charw_")
    atexit.register(shutil.rmtree, d, True)
    subprocess.run(
        [str(EXE), str(src)],
        capture_output=True,
        env={**os.environ, "CLAUDE_SVG": d, "CLAUDE_METRICS_DIR": str(OUT / "metrics")},
    )
    svgs = sorted(Path(d).glob("*.svg"), key=lambda p: int(p.stem))
    doc = fitz.open(pdf)
    if len(svgs) != len(doc):
        return name, None
    acc = defaultdict(list)
    absd = defaultdict(list)
    for sv, pg in zip(svgs, doc):
        s = sv.read_text(encoding="utf-8")
        ech = []
        for m in re.finditer(r"<text\b([^>]*)>([^<]*)</text>", s):
            a = m.group(1)
            xy = text_xy(a)
            fm = re.search(r'font-family="&apos;([^&]+)&apos;', a)
            sm = re.search(r'font-size="([\d.]+)"', a)
            t = dec(m.group(2))
            if xy and len(t) == 1:
                meta = (
                    fm.group(1) if fm else "?",
                    round(float(sm.group(1)) * 0.75, 1) if sm else 0,
                )
                ech.append((xy[0] * 0.75, xy[1] * 0.75, t, meta))
        hch = [
            (c["origin"][0], c["origin"][1], c["c"], None)
            for b in pg.get_text("rawdict")["blocks"]
            for ln in b.get("lines", [])
            for sp in ln["spans"]
            for c in sp["chars"]
        ]
        e_rows, h_rows = rows_of(ech), rows_of(hch)
        for k in e_rows.keys() & h_rows.keys():
            e = [t for t in e_rows[k] if not t[1].isspace()]
            h_all = h_rows[k]
            h = [(i, t) for i, t in enumerate(h_all) if not t[1].isspace()]
            if "".join(t[1] for t in e) != "".join(t[1] for _, t in h):
                continue
            for j in range(len(e) - 1):
                (hi, ht), (hi2, ht2) = h[j], h[j + 1]
                gap_spaces = hi2 - hi - 1
                de = e[j + 1][0] - e[j][0]
                dh = ht2[0] - ht[0]
                font, size = e[j][2]
                if gap_spaces == 0:
                    acc[(font, size, e[j][1])].append(de - dh)
                    absd[(font, size, e[j][1])].append((de, dh))
                elif gap_spaces == 1:
                    acc[(font, size, "␣after")].append(de - dh)
    acc["__abs__"] = absd
    return name, acc


files = sorted(p.stem for p in (OUT / "left" / "in").glob("*.hwpx"))
if ids:
    files = [f for f in files if f in ids]
total = defaultdict(list)
absall = defaultdict(list)
docs = Counter()
with cf.ThreadPoolExecutor(8) as ex:
    for name, acc in ex.map(one, files):
        if acc is None:
            docs["건너뜀"] += 1
            continue
        docs["문서"] += 1
        for k, v in acc.pop("__abs__").items():
            absall[k].extend(v)
        for k, v in acc.items():
            total[k].extend(v)
print(dict(docs), "쌍", sum(len(v) for v in total.values()))
bad = []
for k, v in total.items():
    if len(v) >= 5:
        m = sum(v) / len(v)
        if abs(m) > 0.05:
            bad.append((abs(m) * len(v), k, round(m, 3), len(v)))
for score, k, m, n in sorted(bad, reverse=True)[:top]:
    a = absall.get(k)
    ab = (
        f"  엔진 {sum(x for x, _ in a) / len(a):.3f} 한/글 {sum(y for _, y in a) / len(a):.3f}"
        if a
        else ""
    )
    print(f"{k[0]:12s} {k[1]:5.1f}pt {k[2]!r:10s} 평균 {m:+.3f}pt  {n}쌍{ab}")
