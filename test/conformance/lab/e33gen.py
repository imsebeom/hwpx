"""e33: KEEP_WORD 문단에서 「•」 둘레 꺾는 자리. d034 글을 오른쪽 여백 사다리로 줄 폭만 바꿔 담는다(함초롬바탕 10pt)."""

import json

L = ("HANGUL", "LATIN", "HANJA", "JAPANESE", "OTHER", "SYMBOL", "USER")
TXT = "더 나은 세상을 찾는 마을•체험•독서•진로 교육"
out, meta = [], []
for mode in ("KEEP_WORD", "BREAK_WORD"):
    for i, right in enumerate(range(26000, 33001, 250)):
        name = f"e33_{mode[0]}{i:02d}"
        out.append(
            {
                "name": name,
                "langFaces": {k: "함초롬바탕" for k in L},
                "height": 1000,
                "align": "JUSTIFY",
                "breakNonLatinWord": mode,
                "breakLatinWord": "KEEP_WORD",
                "right": right,
                "paras": ["", TXT],
            }
        )
        meta.append([name, mode, right])
json.dump(out, open("e33.json", "w", encoding="utf-8"), ensure_ascii=False)
json.dump(meta, open("e33_meta.json", "w", encoding="utf-8"), ensure_ascii=False)
print(len(out))
