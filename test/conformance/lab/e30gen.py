"""e30: 글머리표 자리 폭. 글머리 문자(ASCII, 전각 기호, 기호 글꼴 전용 영역 U+F0xx) x 글꼴 x 본문과의 거리."""

import json

L = ("HANGUL", "LATIN", "HANJA", "JAPANESE", "OTHER", "SYMBOL", "USER")
TXT = "가나다라마바사아자차카타파하" * 3
CHARS = ["-", "▶", "●", "", "", "", "※", "o"]
FACES = ["함초롬바탕", "휴먼명조", "맑은 고딕"]
out, meta = [], []
for fi, face in enumerate(FACES):
    for ci, ch in enumerate(CHARS):
        for oi, off in enumerate((50, 0)):
            name = f"e30_{fi}{ci}{oi}"
            out.append(
                {
                    "name": name,
                    "langFaces": {k: face for k in L},
                    "height": 2000,
                    "align": "LEFT",
                    "bullet": {"char": ch, "offset": off},
                    "paras": [TXT],
                }
            )
            meta.append([name, face, f"U+{ord(ch):04X}", off])
json.dump(out, open("e30.json", "w", encoding="utf-8"), ensure_ascii=False)
json.dump(meta, open("e30_meta.json", "w", encoding="utf-8"), ensure_ascii=False)
print(len(out))
