"""e7 분석: 글자마다 한/글이 어느 언어 범주의 글꼴로 폭을 재는지 가린다.

    python e7an.py <e7 재저장 폴더(PDF)> [출력.json]

e7_base 는 일곱 범주 모두 휴먼명조, e7_<범주> 는 그 범주만 Courier New 다. 한 줄 = 한 문단 = 「가X나X…」 또는
「aXbX…」 이므로 줄의 둘째 글자가 시험 글자, 첫 글자가 문맥이다. 시험 글자의 전진 폭이 base 와 0.3pt 넘게
달라지는 범주가 그 글자의 범주다. 어느 범주에서도 안 바뀌면 두 글꼴 폭이 같아 가릴 수 없는 것(「?」).
"""

import glob
import json
import os
import statistics
import sys

import fitz

sys.stdout.reconfigure(encoding="utf-8")
LANGS = ["HANGUL", "LATIN", "HANJA", "JAPANESE", "OTHER", "SYMBOL", "USER"]


def lines(pdf):
    out = {}
    for pg in fitz.open(pdf):
        for b in pg.get_text("rawdict")["blocks"]:
            for ln in b.get("lines", []):
                ch = [c for s in ln["spans"] for c in s["chars"]]
                if len(ch) < 4:
                    continue
                ctx, sym = ch[0]["c"], ch[1]["c"]
                adv = [
                    ch[i + 1]["origin"][0] - ch[i]["origin"][0]
                    for i in range(len(ch) - 1)
                    if ch[i]["c"] == sym
                ]
                if adv:
                    out[(sym, "한" if ctx == "가" else "라")] = statistics.median(adv)
    return out


def main():
    d = sys.argv[1]
    data = {
        os.path.basename(p)[3:-4]: lines(p)
        for p in glob.glob(os.path.join(d, "e7_*.pdf"))
    }
    base = data["base"]
    res = {}
    for key, w in sorted(base.items()):
        cats = [
            L
            for L in LANGS
            if L in data and key in data[L] and abs(data[L][key] - w) > 0.3
        ]
        res[f"{key[0]}|{key[1]}"] = {"base": round(w, 2), "cats": cats}
    by = {}
    for k, v in res.items():
        sym, ctx = k.rsplit("|", 1)
        by.setdefault(sym, {})[ctx] = "+".join(v["cats"]) or "?"
    for sym, v in by.items():
        print(
            f"{sym} U+{ord(sym):04X}  한글 문맥:{v.get('한', '-'):10s} 라틴 문맥:{v.get('라', '-')}"
        )
    if len(sys.argv) > 2:
        json.dump(
            by, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1
        )


if __name__ == "__main__":
    main()
