"""2026-10-23 숫자, 라틴 뒤 기호 앞뒤 꺾기 실험(make.py 변형 json).

    python exp/make_symbreak.py <출력 폴더>   → sb.json
d110, d155 「인프라·101.25|㎡ 단일」: 한/글은 숫자와 ㎡ 사이에서 꺾고 엔진은 「라·101.25㎡」 를 통째로 넘긴다.
문단마다 「가」 k 개 + 빈칸 + 시험 낱말 + 「 끝」. 글자 단위(KEEP_WORD)와 어절 단위(BREAK_WORD) 둘.
"""

import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
TOKENS = [
    "12345678㎡가나다라",
    "abcdefgh㎡가나다라",
    "12345678℃가나다라",
    "12345678%가나다라",
    "12345678→가나다라",
    "12345678※가나다라",
    "12345678①가나다라",
    "12345678○가나다라",
    "가나다라마㎡12345678",
    "가나다라마→abcdefgh",
]
paras = []
for tok in TOKENS:
    for k in range(32, 44):
        paras.append("가" * k + " " + tok + " 끝")
json.dump(
    [
        {
            "name": f"sb_{m[0].lower()}",
            "face": "함초롬바탕",
            "align": "LEFT",
            "breakNonLatinWord": m,
            "paras": paras,
        }
        for m in ("KEEP_WORD", "BREAK_WORD")
    ],
    open(out / "sb.json", "w", encoding="utf-8"),
    ensure_ascii=False,
)
print(len(paras), "문단 x 2")
