"""2026-10-23 d110 문단 139 「Operation Zone(교사」 재현: 휴먼명조 + HCI Poppy 15pt, 줄 폭 45688(실제와 같게).

    python exp/make_paren2.py <출력 폴더>   → pc.json
실험 pa, pb(같은 글꼴 한 벌)에서는 라틴 낱말이 들어가고 「(」 만 넘치면 「(」 앞에서 꺾었는데, d110 은 「Zone」 앞에서 꺾었다.
기호(→, ㎡) 폭 탓인지, 한글과 라틴 글꼴이 다른 탓인지 가른다.
"""

import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
T = "  - 준비실(26.4㎡, 1998년) 분리 구조 → 본 사업 Operation Zone(교사·기자재 보관)으로 자연스럽게 활용"
paras = [
    T,
    T.replace("→", "가"),
    T.replace("㎡", "가"),
    T.replace("→", "가").replace("㎡", "가"),
]
for k in range(18, 30):
    paras.append("가" * k + " 본 사업 Operation Zone(교사·기자재 보관)으로 끝")
# 앞부분을 두고 사이 「가」 수만 바꾼다(줄 끝이 「(」 에 걸리는 k 가 있는지)
for pre in (
    "  - 준비실(26.4㎡, 1998년) 분리 구조 ",
    "  - 준비실가26.4㎡, 1998년가 분리 구조 ",
    "  - 준비실(가가가가, 가가가가년) 분리 구조 ",
):
    for k in range(6, 16):
        paras.append(pre + "가" * k + " Zone(교사·기자재 보관)으로 끝")
base = {
    "height": 1500,
    "align": "JUSTIFY",
    "breakNonLatinWord": "KEEP_WORD",
    "right": -3168,
    "fontType": "HFT",
    "paras": paras,
}
json.dump(
    [
        {
            **base,
            "name": "pc_hp",
            "langFaces": {
                "HANGUL": "휴먼명조",
                "LATIN": "HCI Poppy",
                "SYMBOL": "휴먼명조",
            },
        },
        {
            **base,
            "name": "pc_hh",
            "langFaces": {
                "HANGUL": "휴먼명조",
                "LATIN": "휴먼명조",
                "SYMBOL": "휴먼명조",
            },
        },
    ],
    open(out / "pc.json", "w", encoding="utf-8"),
    ensure_ascii=False,
)
