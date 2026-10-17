"""e32: 점 모양 문자의 줄머리 금칙. 한 줄(20pt 함초롬바탕, 한글 21자 + 남는 폭 1,780)을 한글과 숫자로 채워 점 문자가 줄 끝을 넘게 한다.

문단마다 「가 x 21 + 채움 + 점 + 나 x 10」. 채움 「1」 하나(약 1,100)면 남는 폭이 680 안팎이라 반각 점(1,000)도 못 들어간다.
첫 문단은 구역 정의 부호 16칸이 줄 시작에 더해지므로 빈 문단으로 둔다.
"""

import json

L = ("HANGUL", "LATIN", "HANJA", "JAPANESE", "OTHER", "SYMBOL", "USER")
DOTS = ["•", "·", "‧", "・", "ㆍ", "∙", "･", "●", "※"]
FILLS = ["", "1", "11", "111"]
out, meta = [], []
for i, ch in enumerate(DOTS):
    name = f"e32_{i}"
    paras = [""] + ["가" * 21 + f + ch + "나" * 10 for f in FILLS]
    out.append(
        {
            "name": name,
            "langFaces": {k: "함초롬바탕" for k in L},
            "height": 2000,
            "align": "LEFT",
            "breakNonLatinWord": "BREAK_WORD",
            "paras": paras,
        }
    )
    meta.append([name, f"U+{ord(ch):04X}"])
json.dump(out, open("e32.json", "w", encoding="utf-8"), ensure_ascii=False)
json.dump(meta, open("e32_meta.json", "w", encoding="utf-8"), ensure_ascii=False)
print(len(out))
