"""불일치 문단을 원인 종류로 나눈다. python classify.py [out/score]

원인 칸(한 문단은 하나로만 센다, 위에서부터 먼저 맞는 것):
  글꼴폭없음   엔진에 폭 표가 없는 글꼴(설치 글꼴 등록에 기대는 글꼴)
  조판부호     탭이나 개체(표, 그림, 필드 등)가 낀 문단
  줄수다름     첫 어긋남 자리에서 한쪽만 줄이 끝남(rhwp 가 줄을 더 만들거나 덜 만듦)
  일찍끊음1-3  rhwp 가 한/글보다 1~3 칸 앞에서 끊음(글자 폭 누적, 자간 압축 차이 의심)
  늦게끊음1-3  rhwp 가 1~3 칸 뒤에서 끊음
  크게어긋남   4칸 이상 차이(단어 나눔, 금칙 규칙 차이 의심)
문서 쏠림도 함께 낸다(한 문서가 원인을 부풀리는지).
"""

import collections
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def cause(m):
    if m["metric"] == "엔진표없음":
        return "글꼴폭없음"
    if m["tab"] or m["ctrl"]:
        return "조판부호"
    if m["delta"] is None:
        return "줄수다름"
    if -3 <= m["delta"] < 0:
        return "일찍끊음1-3"
    if 0 < m["delta"] <= 3:
        return "늦게끊음1-3"
    return "크게어긋남"


def main(d):
    d = Path(d)
    M = [
        json.loads(line)
        for line in open(d / "mismatches.jsonl", encoding="utf-8")
        if line.strip()
    ]
    by = collections.defaultdict(list)
    for m in M:
        by[cause(m)].append(m)
    rows = []
    for c, ms in sorted(by.items(), key=lambda x: -len(x[1])):
        docs = collections.Counter(x["id"] for x in ms)
        faces = collections.Counter(x["face"] for x in ms).most_common(3)
        top_doc, top_n = docs.most_common(1)[0]
        rows.append(
            {
                "원인": c,
                "문단": len(ms),
                "문서": len(docs),
                "본문": sum(x["where"] == "본문" for x in ms),
                "칸": sum(x["where"] == "칸" for x in ms),
                "가장 많은 문서": f"{top_doc}({top_n})",
                "주요 글꼴": ", ".join(f"{f}({n})" for f, n in faces),
                "예": [x["text"][:40] for x in ms[:3]],
            }
        )
    (d / "causes.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(f"불일치 문단 {len(M)}")
    for r in rows:
        print(
            f"{r['원인']:8} {r['문단']:5}문단 {r['문서']:3}문서 (본문 {r['본문']}, 칸 {r['칸']}) 쏠림 {r['가장 많은 문서']} | {r['주요 글꼴']}"
        )


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "out" / "score")
