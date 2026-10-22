"""2026-10-23 한컴 내장 글꼴 굵게 폭 늘림이 크기, 장평, 자간에 따라 어떻게 변하는지(make.py 변형 json).

    python exp/make_boldhft2.py <출력 폴더>   → bh2.json
실험 bh: 한양중고딕 등 T1 로 박히는 내장 글꼴은 굵게면 글자마다 10pt 에서 약 48HU 늘어난다(보통 1000 → 1048).
"""

import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
para = "가나다라마바사아자차카타파하 abcdefghij 0123456789"
vs = []
for h in (800, 1000, 1400, 2000):
    for r, s in ((100, 0), (90, 0), (100, -10), (90, -10)):
        for b in (0, 1):
            vs.append(
                {
                    "name": f"bi_{h}_{r}_{abs(s)}_{b}",
                    "face": "한양중고딕",
                    "fontType": "HFT",
                    "height": h,
                    "ratio": r,
                    "spacing": s,
                    "bold": bool(b),
                    "align": "LEFT",
                    "paras": [para],
                }
            )
json.dump(vs, open(out / "bh2.json", "w", encoding="utf-8"), ensure_ascii=False)
print(len(vs), "문서")
