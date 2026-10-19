"""make_charcal.py 문서의 글자 전진 폭(같은 글자 묶음 평균, pt)을 한/글 PDF 와 네이티브 엔진 SVG 로 견준다.

    python exp/read_charcal.py <폴더: in/charcal.hwpx, rt/charcal.pdf, in/variants.txt> [--all]

변형(글꼴, 장평, 자간)마다 글자별 한/글, 엔진, 차를 찍는다. --all 이 없으면 차가 0.02pt 넘는 것만. 「가␣」 는 가 + 빈칸.
"""

import os
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

import fitz
from svgpos import text_xy

sys.stdout.reconfigure(encoding="utf-8")
base = Path(sys.argv[1])
show_all = "--all" in sys.argv
EXE = (
    Path.home()
    / ".claude/skills/hwpx/editor/.build/rhwp/target/debug/claude-linestarts.exe"
)
variants = {
    int(k): (f, r, s)
    for k, f, r, s in (
        ln.split("\t")
        for ln in (base / "in" / "variants.txt")
        .read_text(encoding="utf-8")
        .splitlines()
    )
}


def lines_in_order(pages):
    """pages: [[(x, y, c)]] → 쪽 순서, 줄(y) 순서, x 순서의 [(x, c)] 줄 목록"""
    out = []
    for chars in pages:
        rows = defaultdict(list)
        for x, y, c in chars:
            rows[round(y, 1)].append((x, c))
        for y in sorted(rows):
            out.append(sorted(rows[y]))
    return out


def measure(lines):
    res = defaultdict(list)
    cur = None
    for ln in lines:
        txt = "".join(c for _, c in ln)
        for m in re.finditer(r"◆(\d\d)◆", txt):
            cur = int(m.group(1))
        if cur is None:
            continue
        vis = [(x, c) for x, c in ln if not c.isspace()]
        i = 0
        while i < len(vis):
            j = i
            while j + 1 < len(vis) and vis[j + 1][1] == vis[i][1]:
                j += 1
            n = j - i + 1
            c = vis[i][1]
            if n >= 4 and c not in "|◆가":
                key = "가␣" if c == "가" and n == 8 and False else c
                res[(cur, key)].append(((vis[j][0] - vis[i][0]) / (n - 1), n - 1))
            i = j + 1
        # 「가 가 가」: 빈칸을 낀 가 묶음(PDF 는 빈칸 글자가 있고 SVG 는 없다 — 둘 다 빈칸 뺀 가 사이 간격)
        ga = [x for x, c in vis if c == "가"]
        if txt.count("가 가") >= 3 or (
            "가가" not in txt and len(ga) >= 4 and "가 " in txt
        ):
            pass
    return res


def ga_space(lines):
    res = defaultdict(list)
    cur = None
    for ln in lines:
        txt = "".join(c for _, c in ln)
        for m in re.finditer(r"◆(\d\d)◆", txt):
            cur = int(m.group(1))
        if cur is None:
            continue
        vis = [(x, c) for x, c in ln if not c.isspace()]
        idx = [k for k, (_, c) in enumerate(vis) if c == "가"]
        # 줄 끝의 「가 가 …」: 연속 인덱스이고 원문에서 빈칸으로 떨어진 묶음
        tail = []
        for k in reversed(idx):
            if tail and k != tail[-1] - 1:
                break
            tail.append(k)
        tail.reverse()
        if len(tail) >= 4 and "가 가" in txt:
            xs = [vis[k][0] for k in tail]
            res[(cur, "가␣")].append(((xs[-1] - xs[0]) / (len(xs) - 1), len(xs) - 1))
    return res


def avg(v):
    w = sum(n for _, n in v)
    return sum(a * n for a, n in v) / w if w else None


doc = fitz.open(base / "rt" / "charcal.pdf")
hp = [
    [
        (c["origin"][0], c["origin"][1], c["c"])
        for b in pg.get_text("rawdict")["blocks"]
        for ln in b.get("lines", [])
        for s in ln["spans"]
        for c in s["chars"]
    ]
    for pg in doc
]
d = tempfile.mkdtemp(prefix="charcal_")
subprocess.run(
    [str(EXE), str(base / "in" / "charcal.hwpx")],
    capture_output=True,
    # 에디터와 같은 조건: dump_metrics.mjs 로 뽑은 글꼴 폭 표(<폴더>/m/charcal.json)
    env={**os.environ, "CLAUDE_SVG": d, "CLAUDE_METRICS_DIR": str(base / "m")},
)
ep = []
for sv in sorted(Path(d).glob("*.svg"), key=lambda p: int(p.stem)):
    s = sv.read_text(encoding="utf-8")
    page = []
    for m in re.finditer(r"<text\b([^>]*)>([^<]*)</text>", s):
        xy = text_xy(m.group(1))
        t = m.group(2)
        if xy and len(t) == 1:
            page.append((xy[0] * 0.75, xy[1] * 0.75, t))
    ep.append(page)
hl, el = lines_in_order(hp), lines_in_order(ep)
H, E = measure(hl), measure(el)
H.update(ga_space(hl))
E.update(ga_space(el))
for k in sorted(variants):
    f, r, s = variants[k]
    rows = []
    for (vk, c), v in sorted(H.items()):
        if vk != k or (vk, c) not in E:
            continue
        a, b = avg(v), avg(E[(vk, c)])
        if show_all or abs(b - a) > 0.02:
            rows.append(f"{c}:{a:.3f}/{b:.3f}({b - a:+.3f})")
    print(f"{k:02d} {f} 장평{r} 자간{s}: " + "  ".join(rows))
