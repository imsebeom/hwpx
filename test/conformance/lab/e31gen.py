"""e31: 글머리표가 첫 줄 폭을 줄이지 않는 조건 찾기(d302 p100: 한/글 첫 줄 글 폭 46,356 ≈ 줄 폭 46,988, 글머리표 자리 1,650 을 안 뺌).

바꾸는 것: 글머리표 글자 모양(문단 것 / 11pt / 0pt), 왼쪽 오른쪽 여백(0 / 700, 500), 글 첫 글자 빈칸. 본문 14pt 휴먼명조.
"""

import json

L = ("HANGUL", "LATIN", "HANJA", "JAPANESE", "OTHER", "SYMBOL", "USER")
TXT = "가나다라마바사아자차카타파하" * 4
CASES = [
    ("base", {}, {}, TXT),
    ("ch11", {"charHeight": 1100}, {}, TXT),
    ("ch0", {"charHeight": 0}, {}, TXT),
    ("margin", {}, {"left": 700, "right": 500}, TXT),
    ("space", {}, {}, " " + TXT),
    ("all", {"charHeight": 1100}, {"left": 700, "right": 500}, " " + TXT),
]
out, meta = [], []
for i, (nm, bl, extra, txt) in enumerate(CASES):
    name = f"e31_{i:02d}"
    out.append(
        {
            "name": name,
            "langFaces": {k: "휴먼명조" for k in L},
            "height": 1400,
            "align": "JUSTIFY",
            "bullet": {"char": "", "offset": 50, **bl},
            "paras": [txt],
            **extra,
        }
    )
    meta.append([name, "휴먼명조", nm])
json.dump(out, open("e31.json", "w", encoding="utf-8"), ensure_ascii=False)
json.dump(meta, open("e31_meta.json", "w", encoding="utf-8"), ensure_ascii=False)
print(len(out))
