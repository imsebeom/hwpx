"""e30(번호 문단 머리 폭) 읽기: 줄마다 첫 글자 x, 첫 「가」 x, 글자 수. 단위 pt(PDF 눈금 그대로)."""
import json
import sys

import fitz

sys.stdout.reconfigure(encoding="utf-8")
meta = json.load(open("e30_meta.json", encoding="utf-8"))
for name, face, *case in meta:
    d = fitz.open(f"../out/lab/e30_rt/{name}.pdf")
    rows = []
    for pg in d:
        for b in pg.get_text("rawdict")["blocks"]:
            for ln in b.get("lines", []):
                ch = [c for s in ln["spans"] for c in s["chars"]]
                if not ch:
                    continue
                g = next((c for c in ch if c["c"] == "가"), None)
                head = "".join(c["c"] for c in ch[: ch.index(g)]) if g else ""
                rows.append((round(ch[0]["origin"][0], 2), round(g["origin"][0], 2) if g else None, len(ch), head))
    print(f"{name} {face:6s} {str(case):18s}", " | ".join(f"{x0} {gx} n{n} {h!r}" for x0, gx, n, h in rows))
