"""e15 측정(한/글 2024 PDF)에서 함초롬바탕, 함초롬돋움의 글자 폭(1000 단위 em)을 뽑는다.

    python e15an.py <e15 재저장 폴더> <출력.json>

문단 「가X가X가X가X가」(40pt) 마다 첫 「가」와 끝 「가」 사이를 4로 나눈 값에서 「가」 폭(0.970em, e14 실측)을 뺀다
(PDF 좌표 눈금 0.06pt 의 오차를 1/4 로 줄인다).
X 글리프가 PDF 에 찍히지 않아도(폭 없는 글자, 대체 글꼴) 간격으로 잴 수 있다. 줄은 쪽, y 순서로 문단에 맞댄다.
"""

import collections
import json
import os
import sys

import fitz

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
SIZE, GA = 40.0, 970.0
# PDF 좌표는 조판 값의 0.99946 배다(ASCII 768자를 엔진 내장 표와 맞대어 잰 배율, 두 글꼴 같음)
SCALE = 0.99946


def rows(pdf):
    out = []
    for pg in fitz.open(pdf):
        by = collections.defaultdict(list)
        for b in pg.get_text("rawdict")["blocks"]:
            for ln in b.get("lines", []):
                for s in ln["spans"]:
                    for c in s["chars"]:
                        by[round(c["origin"][1])].append((c["origin"][0], c["c"]))
        for y in sorted(by):
            if sum(1 for _, ch in by[y] if ch == "가") >= 2:
                out.append(sorted(by[y]))
    return out


def main(rt, dst):
    meta = json.load(open(os.path.join(HERE, "e15_meta.json"), encoding="utf-8"))
    chars = meta["chars"]
    res = {}
    for i, font in enumerate(meta["fonts"]):
        rs = rows(os.path.join(rt, f"e15_{i}.pdf"))
        if len(rs) != len(chars):
            print(font, "줄 수가 문단 수와 다르다", len(rs), len(chars))
        widths = {}
        for ch, row in zip(chars, rs):
            xs = [x for x, c in row if c == "가"]
            if ch == "!":
                # 한/글은 「!」 뒤에 한글이 오면 빈칸 글자를 하나 더 찍고 약 0.18em 을 띄운다. 「!」 자체 폭은 다음 글자까지로 잰다
                i = next(k for k, (_, c) in enumerate(row) if c == "!")
                widths[ch] = round((row[i + 1][0] - row[i][0]) / SCALE / SIZE * 1000, 1)
            elif len(xs) == 5:
                widths[ch] = round((xs[-1] - xs[0]) / 4 / SCALE / SIZE * 1000 - GA, 1)
        res[font] = widths
        print(font, "잰 글자", len(widths))
    json.dump(res, open(dst, "w", encoding="utf-8"), ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
