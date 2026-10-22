"""2026-10-22 줄 나눔 규칙 실험(make.py 변형 json)을 만든다.

    python exp/make_breakrules.py <출력 폴더>   → mg.json, gg.json, cj.json, ts.json, t2.json
    python make.py <출력>/<이름>.json <입력 폴더>  (cj 는 만든 뒤 글자 단위 사본 cj_c 를 따로 만든다: 문단 모양 0 의
    breakNonLatinWord 를 KEEP_WORD 로) → hwpx_lab/measure.py → 재저장본 줄 배치(textpos)를 엔진(claude-linestarts, CLAUDE_METRICS_DIR)과 견준다.

mg: 맑은 고딕, 함초롬바탕 x 장평/자간 다섯 조합의 「・」, 「·」, 한글 폭(rhwpadv 는 커서가 1px 단위라 줄 글자 수로 본다)
gg: 「가」만, 「가・」, 「・」만, 「가ㆍ」 줄 글자 수
cj: 어절 단위에서 한글과 한자, ・ 가 섞인 빈칸 없는 묶음
ts: 「가」41~43 + 끝 빈칸 1~6 (왼쪽, 양쪽, 가운데)
t2: 「가」43 + i 0~4개 + 끝 빈칸 1~3, 「가」44 + 끝 빈칸 1~4
"""

import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)


def dump(name, variants):
    (out / f"{name}.json").write_text(
        json.dumps(variants, ensure_ascii=False), encoding="utf-8"
    )


mg_paras = [
    "인문・과학・예체능교육 수학・과학・AI・디지털 독서·토론・인문교육 Ⅲ-2. 가나다라마바사 한글 문장",
    "가・" * 26,
] * 2
dump(
    "mg",
    [
        {
            "name": f"mg_{'m' if f == '맑은 고딕' else 'h'}_{r}_{abs(s)}",
            "face": f,
            "ratio": r,
            "spacing": s,
            "align": "LEFT",
            "paras": mg_paras,
        }
        for f in ("맑은 고딕", "함초롬바탕")
        for r, s in ((100, 0), (96, 0), (100, -10), (96, -10), (92, -20))
    ],
)
dump(
    "gg",
    [
        {
            "name": f"gg_{t}",
            "face": f,
            "align": "LEFT",
            "paras": ["가" * 60, "가・" * 30, "・" * 60, "가ㆍ" * 30],
        }
        for f, t in (("함초롬바탕", "h"), ("맑은 고딕", "m"))
    ],
)
dump(
    "cj",
    [
        {
            "name": "cj_w",
            "face": "함초롬바탕",
            "align": "LEFT",
            "paras": [
                "가・" * 30,
                "가漢" * 30,
                "가가가・" * 15,
                "가가가漢" * 15,
                "漢가가가" * 15,
                "・가가가" * 15,
            ],
        }
    ],
)
ts_paras = ["가" * n + " " * k for n in (41, 42, 43) for k in range(1, 7)]
dump(
    "ts",
    [
        {
            "name": f"ts_{a[0].lower()}",
            "face": "함초롬바탕",
            "align": a,
            "paras": ts_paras,
        }
        for a in ("LEFT", "JUSTIFY", "CENTER")
    ],
)
t2_paras = [
    "가" * 43 + tail + " " * k
    for tail in ("", "i", "ii", "iii", "iiii")
    for k in (1, 2, 3)
]
t2_paras += ["가" * 44 + " " * k for k in (1, 2, 3, 4)]
dump(
    "t2",
    [
        {
            "name": f"t2_{a[0].lower()}",
            "face": "함초롬바탕",
            "align": a,
            "paras": t2_paras,
        }
        for a in ("LEFT", "CENTER")
    ],
)
print("ok")
