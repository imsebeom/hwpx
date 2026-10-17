"""e21 처럼 한 글꼴의 전체 구간을 잰 실험(e20an.py 출력)으로 hft-metrics.json 항목을 만들어 넣는다(같은 이름은 바꾼다).

    python build_hft_full.py <e21_han.json> <hft-metrics.json>

PDF 좌표 눈금이 글꼴마다 조금 달라, 그 글꼴 한글 음절 폭의 중앙값을 1000(전각)으로 보고 다른 글자를 같은 비율로 맞춘다.
한글 음절이 모두 같은 폭이면 그 값을 hangul 로 싣는다. 폭 0 은 표에서 「모름」이라 폭 없는 글자는 1 로 적는다.
"""

import json
import statistics
import sys

sys.stdout.reconfigure(encoding="utf-8")
from build_hcr_metrics import table  # noqa: E402


def main(src, dst):
    han = json.load(open(src, encoding="utf-8"))
    entries = []
    for font, rec in han.items():
        w = rec["w"]
        syl = [v for c, v in w.items() if "가" <= c <= "힣"]
        k = 1000 / statistics.median(syl) if syl else 1.0
        widths = {c: v * k for c, v in w.items() if not ("가" <= c <= "힣")}
        hangul = round(statistics.median(syl) * k) if syl else None
        entries.append({"name": font, "bold": False, "em": 1000, "hangul": hangul, "ranges": table(widths)})
        print(font, "보정", round(k, 5), "한글", hangul, "글자", len(widths))
    old = json.load(open(dst, encoding="utf-8"))
    names = {e["name"] for e in entries}
    merged = [e for e in old if e["name"] not in names] + entries
    json.dump(merged, open(dst, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"{len(merged)}개 글꼴 → {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
