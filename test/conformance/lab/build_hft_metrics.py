"""e9 측정(한/글 2024 PDF 글자 위치)으로 글꼴 파일이 없는 한컴 내장 글꼴의 폭 표를 만든다.

    python build_hft_metrics.py <e9 재저장 폴더> <출력 hft-metrics.json>

40pt 문단 「가X가X…」 의 X 전진 폭 중앙값 ÷ 40pt = em 비율을 1000 단위로 싣는다.
형식은 엔진 registerFontMetrics 와 같다: {name, bold, em, hangul, ranges:[[시작 코드, [폭…]]]}.
빈칸은 넣지 않는다(실험이 useFontSpace=0 이라 반각만 보였다. 엔진이 반각 규칙을 따로 쓴다).
"""

import json
import os
import statistics
import sys

import fitz

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
SIZE, PDF_SCALE = 40.0, 1.0  # 10pt 의 0.9955 는 좌표 눈금(약 0.12pt) 오차였다. 40pt 에서는 0.05% 라 보정하지 않는다


def advances(pdf):
    got = {}
    for pg in fitz.open(pdf):
        for b in pg.get_text("rawdict")["blocks"]:
            for ln in b.get("lines", []):
                ch = [c for s in ln["spans"] for c in s["chars"]]
                if len(ch) < 4 or ch[0]["c"] != "가":
                    continue
                sym = ch[1]["c"]
                adv = [
                    ch[i + 1]["origin"][0] - ch[i]["origin"][0]
                    for i in range(len(ch) - 1)
                    if ch[i]["c"] == sym and ch[i + 1]["c"] == "가"
                ]
                if adv:
                    got[sym] = statistics.median(adv)
    return got


def main():
    src, out = sys.argv[1], sys.argv[2]
    meta = json.load(open(os.path.join(HERE, "e9_meta.json"), encoding="utf-8"))
    result = []
    for i, font in enumerate(meta["fonts"]):
        pdf = os.path.join(src, f"e9_{i:02d}.pdf")
        if not os.path.exists(pdf):
            continue
        adv = advances(pdf)
        units = {
            c: round(w / (SIZE * PDF_SCALE) * 1000) for c, w in adv.items() if c != " "
        }
        hangul = [units[c] for c in units if "가" <= c <= "힣"]
        han = round(statistics.median(hangul)) if hangul else None
        codes = sorted(ord(c) for c in units if not ("가" <= c <= "힣"))
        ranges, cur = [], None
        for cp in codes:
            if cur and cp == cur[0] + len(cur[1]):
                cur[1].append(units[chr(cp)])
            elif (
                cur and cp - (cur[0] + len(cur[1])) <= 8
            ):  # 작은 틈은 0(모름)으로 메운다
                cur[1].extend([0] * (cp - (cur[0] + len(cur[1]))))
                cur[1].append(units[chr(cp)])
            else:
                cur = [cp, [units[chr(cp)]]]
                ranges.append(cur)
        spread = (min(hangul), max(hangul)) if hangul else None
        print(
            f"{font}: 글자 {len(units)}, 한글 {han} (범위 {spread}), 「a」{units.get('a')} 「·」{units.get('·')} 「(」{units.get('(')}"
        )
        result.append(
            {"name": font, "bold": False, "em": 1000, "hangul": han, "ranges": ranges}
        )
    json.dump(result, open(out, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"{len(result)}개 글꼴 → {out}")


if __name__ == "__main__":
    main()
