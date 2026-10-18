"""e35: 빈칸 묶음 가운데서 꺾을 때 남은 폭이 빈칸 하나보다 좁아도 한/글이 빈칸 둘을 앞줄에 남기는가.

e34 의 「가」 43자 줄에서 오른쪽 여백(HWPUNIT)을 0~1000 으로 늘려 「가」 뒤 남는 폭을 줄인다(10pt 함초롬바탕 「가」 폭 1000).
빈칸 묶음 1, 2, 3, 5. 정렬 JUSTIFY, 어절 단위. 문서 하나에 여백 하나(여백은 문단 모양이라 문서마다 바꾼다).
"""

import json

L = ("HANGUL", "LATIN", "HANJA", "JAPANESE", "OTHER", "SYMBOL", "USER")
out, meta = [], []
for right in (0, 100, 200, 300, 400, 500, 600, 700, 800, 900):
    name = f"e35_{right}"
    paras = []
    for k in (1, 2, 3, 5):
        paras.append("가" * 43 + " " * k + "나다라마")
        meta.append([name, len(paras) - 1, right, k])
    out.append(
        {
            "name": name,
            "langFaces": {k: "함초롬바탕" for k in L},
            "height": 1000,
            "align": "JUSTIFY",
            "breakLatinWord": "KEEP_WORD",
            "breakNonLatinWord": "KEEP_WORD",
            "right": right,
            "paras": paras,
        }
    )
json.dump(out, open("e35.json", "w", encoding="utf-8"), ensure_ascii=False)
json.dump(meta, open("e35_meta.json", "w", encoding="utf-8"), ensure_ascii=False)
print(len(out), len(meta))
