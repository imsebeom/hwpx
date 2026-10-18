"""make_condense0.py 변형의 한/글 PDF 에서 p121 첫 줄이 「면제」까지 담았는지와 첫 줄 빈칸 평균 폭(pt)을 찍는다.

    python exp/read_condense0.py <폴더: rt/*.pdf>

PDF 는 run 마다 줄을 따로 두므로 「부여 내용」와 기준선 y 가 같은 글자를 모두 모은다.
"""

import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8")
base = Path(sys.argv[1])


def first_line(pdf):
    for pg in fitz.open(pdf):
        chars = [
            c
            for b in pg.get_text("rawdict")["blocks"]
            for ln in b.get("lines", [])
            for s in ln["spans"]
            for c in s["chars"]
        ]
        t = "".join(c["c"] for c in chars)
        i = t.find("부여 내용")
        if i < 0:
            continue
        y = chars[i]["origin"][1]
        line = sorted(
            (c for c in chars if abs(c["origin"][1] - y) < 0.5),
            key=lambda c: c["origin"][0],
        )
        return line
    return None


for pdf in sorted((base / "rt").glob("m_*.pdf")):
    cs = first_line(pdf)
    if not cs:
        print(pdf.stem, "못 찾음")
        continue
    t = "".join(c["c"] for c in cs)
    x = [c["origin"][0] for c in cs]
    sp = [x[i + 1] - x[i] for i, c in enumerate(cs[:-1]) if c["c"] == " " and i >= 2]
    print(
        f"{pdf.stem:16s} 한줄={'예' if '면제' in t else '아니오'} 글자 {len(t):3d} "
        f"빈칸(앞 둘 뺌) 평균 {sum(sp) / max(len(sp), 1):.3f} 최소 {min(sp):.3f} 끝 글자 x {x[-1]:.1f} {t[-6:]!r}"
    )
