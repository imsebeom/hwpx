"""한/글 PDF 의 글자 위치로 글자 종류별 전진 폭(pt)과 줄마다의 글자 수를 잰다.

    python pdfadv.py <PDF 폴더> [출력.json]

글자 하나의 전진 폭 = 같은 줄 다음 글자의 원점 x - 이 글자의 원점 x. 줄의 마지막 글자는 뺀다.
종류별 중앙값을 낸다: 한글 「가」, 빈칸, 라틴 「a」, 숫자 「0」, 마침표.
"""

import glob
import json
import os
import statistics
import sys

import fitz

sys.stdout.reconfigure(encoding="utf-8")


def measure(pdf):
    d = fitz.open(pdf)
    adv = {}
    lines = []
    for pg in d:
        for b in pg.get_text("rawdict")["blocks"]:
            for ln in b.get("lines", []):
                chars = [c for s in ln["spans"] for c in s["chars"]]
                lines.append(
                    {
                        "n": len(chars),
                        "x0": round(chars[0]["origin"][0], 2) if chars else None,
                        "text": "".join(c["c"] for c in chars),
                    }
                )
                for a, b2 in zip(chars, chars[1:]):
                    adv.setdefault(a["c"], []).append(b2["origin"][0] - a["origin"][0])
    pick = {
        k: round(statistics.median(v), 3)
        for k, v in adv.items()
        if os.environ.get("ALL") or k in "가 a0." or k == " "
    }
    return {"adv": pick, "lines": [(ln["n"], ln["text"][-6:]) for ln in lines]}


def main():
    res = {}
    for pdf in sorted(glob.glob(os.path.join(sys.argv[1], "*.pdf"))):
        res[os.path.basename(pdf)[:-4]] = measure(pdf)
    for k, v in res.items():
        print(k, v["adv"], [n for n, _ in v["lines"]])
    if len(sys.argv) > 2:
        json.dump(
            res, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1
        )


if __name__ == "__main__":
    main()
