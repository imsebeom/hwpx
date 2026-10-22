"""2026-10-23 글 속 문자 그대로의 U+00A0(hp:nbSpace 요소가 아닌) 폭과 꺾기 실험(make.py 변형 json).

    python exp/make_nbsp.py <출력 폴더>   → nb.json
d300 「사용자 인증,\\xa0회원가입,\\xa0탈퇴 등」: 빈칸 폭으로 재면 줄을 넘는데 한/글은 한 줄에 담는다.
PDF 글자 위치로 U+00A0 전진 폭을 재고, 「가」 k 개 + U+00A0 낱말로 그 자리에서 꺾는지 본다.
"""

import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
paras = ["가 " * 20 + "끝", "가 " * 20 + "끝", "a " * 20 + "끝"]
for k in range(36, 44):
    paras.append("가" * k + " 가나다라마바 끝")
json.dump(
    [
        {
            "name": f"nb_{t}_{u}",
            "face": f,
            "useFontSpace": u,
            "align": "LEFT",
            "breakNonLatinWord": "BREAK_WORD",
            "paras": paras,
        }
        for f, t in (("함초롬바탕", "h"), ("함초롬돋움", "d"))
        for u in (0, 1)
    ],
    open(out / "nb.json", "w", encoding="utf-8"),
    ensure_ascii=False,
)
