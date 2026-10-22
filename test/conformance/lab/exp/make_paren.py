"""2026-10-23 어절 단위 문단의 괄호, 로마 숫자, 가운뎃점 앞뒤 꺾기 실험(make.py 변형 json).

    python exp/make_paren.py <출력 폴더>   → pa.json
    python make.py <출력>/pa.json <입력 폴더> → hwpx_lab/measure.py → nativescore.py 로 엔진과 견준다.

문단마다 「가」 k 개 + 빈칸 + 시험 낱말 + 「 끝」. k 를 바꿔 줄 끝이 낱말 안 여러 자리에 걸리게 한다.
d229 「chamber|(이중」, d110 「Zone(교사」(안 꺾음), d301 「운영|(10분」, d122 「(Ⅲ|단계」, d155 「AI·|컴퓨터」.
"""

import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)

TOKENS = [
    "abcdefgh(가나다라마)",
    "abcdefgh(abcdefg)",
    "가나다라마(가나다라마)",
    "가나다라마(1234567)",
    "12345678(가나다라마)",
    "가나다(Ⅲ가나다라마)",
    "ABCDE·가나다라마바",
    "가나다라·가나다라마",
    "ABCDE·FGHIJKL",
    "가나다라마바사아자차",
]
paras = []
for tok in TOKENS:
    for k in range(32, 44):
        paras.append("가" * k + " " + tok + " 끝")
TOKENS2 = [
    "Zone(교사·기자재 보관)으로",
    "zone(교사기자재)으로",
    "abcd(가나다라마)",
    "abcdefgh(가나다라마)",
    "Operation Zone(교사기자재)",
    "ABCDEFGH(가나다라마)",
]
paras2 = []
for tok in TOKENS2:
    for k in range(34, 44):
        paras2.append("가" * k + " " + tok + " 끝")
json.dump(
    [
        {
            "name": f"pb_{a[0].lower()}",
            "face": "함초롬바탕",
            "align": a,
            "breakNonLatinWord": "KEEP_WORD",
            "paras": paras2,
        }
        for a in ("LEFT", "JUSTIFY")
    ],
    open(out / "pb.json", "w", encoding="utf-8"),
    ensure_ascii=False,
)
json.dump(
    [
        {
            "name": f"pa_{t}",
            "face": f,
            "align": "LEFT",
            "breakNonLatinWord": "KEEP_WORD",
            "paras": paras,
        }
        for f, t in (("함초롬바탕", "h"), ("맑은 고딕", "m"))
    ],
    open(out / "pa.json", "w", encoding="utf-8"),
    ensure_ascii=False,
)
print(len(paras), "문단 x 2")
