"""e34: 줄 끝 빈칸 묶음을 양쪽 정렬에서 몇 개 앞줄에 남기는가. e19(왼쪽 정렬)와 같은 글을 JUSTIFY, KEEP_WORD 로.

정답본 불일치 40곳 가까이(양쪽 정렬, 어절 단위)에서 한/글은 빈칸 묶음 가운데서 꺾을 때 줄 끝에 빈칸을 늘 2개 남겼다(rhwp 1개).
「가」 42~44자 x 빈칸 1~9개 x 정렬(JUSTIFY, LEFT). 줄 시작은 다시 저장한 HWPX 의 linesegarray textpos 로 읽는다.
"""

import json

L = ("HANGUL", "LATIN", "HANJA", "JAPANESE", "OTHER", "SYMBOL", "USER")
out, meta = [], []
for align in ("JUSTIFY", "LEFT"):
    paras = []
    for n in (42, 43, 44):
        for k in range(1, 10):
            paras.append("가" * n + " " * k + "나다라마")
            meta.append([f"e34_{align[0]}", len(paras) - 1, align, n, k])
    out.append(
        {
            "name": f"e34_{align[0]}",
            "langFaces": {k: "함초롬바탕" for k in L},
            "height": 1000,
            "align": align,
            "breakLatinWord": "KEEP_WORD",
            "breakNonLatinWord": "KEEP_WORD",
            "paras": paras,
        }
    )
json.dump(out, open("e34.json", "w", encoding="utf-8"), ensure_ascii=False)
json.dump(meta, open("e34_meta.json", "w", encoding="utf-8"), ensure_ascii=False)
print(len(out), len(meta))
