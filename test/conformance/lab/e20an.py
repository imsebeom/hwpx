"""e20 측정(한/글 2024 PDF, 글꼴 12종 × 기호 160자, 40pt)에서 글자 폭(1000 단위 em)을 뽑는다.

    python e20an.py <재저장 폴더> <출력.json> [실험 이름=e20]   (e21 처럼 같은 꼴의 실험도 된다)

문단 「가X가X가X가X가」 마다 첫 「가」와 끝 「가」 사이를 4로 나눈 값에서 「가」 폭을 뺀다. 「가」 폭은 그 글꼴에서 「가」 다음에
X 가 찍힌 줄들의 중앙값이다. 줄이 빠지거나(한 줄이 두 줄로 묶임) 글자가 안 찍히는 경우가 있어 줄과 문단은 찍힌 글자로 맞댄다.
"""

import json
import os
import statistics
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e15an import rows  # noqa: E402

SCALE = 0.99946


def main(rt, dst, name="e20"):
    meta = json.load(
        open(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)), f"{name}_meta.json"
            ),
            encoding="utf-8",
        )
    )
    chars = meta["chars"]
    out = {}
    for i, font in enumerate(meta["fonts"]):
        pdf = os.path.join(rt, f"{name}_{i:02d}.pdf")
        if not os.path.exists(pdf):
            pdf = os.path.join(rt, f"{name}_{i}.pdf")
        rs = rows(pdf)
        ga = [
            row[k + 1][0] - row[k][0]
            for row in rs
            for k in range(len(row) - 1)
            if row[k][1] == "가" and row[k + 1][1] != "가"
        ]
        gaw = statistics.median(ga)
        w, ri = {}, 0
        for ci, ch in enumerate(chars):
            if ri >= len(rs):
                break
            others = {c for _, c in rs[ri] if c != "가"}
            if others and ch not in others and others & set(chars[ci + 1 : ci + 4]):
                # 이 줄은 뒤에 올 글자의 줄이다 — 이 글자 줄이 빠졌다고 보고 넘어간다
                # (뒤 글자와도 안 맞으면 PDF 가 이 글자를 다른 코드로 찍은 것으로 보고 이 줄을 쓴다)
                continue
            xs = [x for x, c in rs[ri] if c == "가"]
            if len(xs) == 5:
                w[ch] = round(((xs[-1] - xs[0]) / 4 - gaw) / SCALE / 40 * 1000, 1)
            ri += 1
        out[font] = {"ga": round(gaw / SCALE / 40 * 1000, 1), "w": w}
        print(font, "가", out[font]["ga"], "잰 글자", len(w), "줄", len(rs))
    json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False)


if __name__ == "__main__":
    main(*sys.argv[1:4])
