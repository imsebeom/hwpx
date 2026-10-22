"""2026-10-23 한컴 내장 글꼴(HFT)의 굵게 폭 실험(make.py 변형 json).

    python exp/make_boldhft.py <출력 폴더>   → bh.json
d317(한양중고딕): 같은 자간 -4% 에서 보통 「연구」 964HU, 굵은 「참고」 1013HU(10pt). e11 은 TTF 글꼴만 봐서 「굵게도 보통 폭」
(bold-regular-width)으로 정했다. 내장 글꼴마다 보통, 굵게 글 한 줄을 두고 PDF 전진 폭을 견준다.
"""

import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
FACES = [
    "한양중고딕",
    "한양신명조",
    "한양견고딕",
    "휴먼명조",
    "HCI Poppy",
    "신명 중고딕",
    "신명 태명조",
    "명조",
    "산세리프",
]
para = "가나다라마바사아자차카타파하 abcdefghij ABCDEFG 0123456789 ()·,."
json.dump(
    [
        {
            "name": f"bh_{i}_{b}",
            "face": f,
            "fontType": "HFT",
            "bold": bool(b),
            "align": "LEFT",
            "paras": [para],
        }
        for i, f in enumerate(FACES)
        for b in (0, 1)
    ],
    open(out / "bh.json", "w", encoding="utf-8"),
    ensure_ascii=False,
)
print(len(FACES) * 2, "문서")
