"""e15 측정으로 함초롬바탕, 함초롬돋움의 폭 표를 만들어 에디터 hft-metrics.json 에 넣는다(같은 이름은 바꾼다).

    python build_hcr_metrics.py <e15_han.json> <hft-metrics.json>

함초롬 계열은 이 PC 에 글꼴 파일이 없고 엔진 내장 표가 있다. 내장 표에 없는 기호(①, →, Ⅰ 등 121자)를 엔진은 전각 1em 으로
어림하는데 한/글은 0.970em 으로 잰다. 함초롬돋움은 내장 표의 일반 문장 부호 67자(…, —, • 등)도 한/글과 다르다.
한글 음절은 e14 에서 1,170자 모두 0.970em 이었다. 폭 0 은 표에서 「모름」이라, 폭 없는 결합 문자는 1 로 적는다.
"""

import json
import sys

sys.stdout.reconfigure(encoding="utf-8")


def table(widths):
    units = {c: max(1, round(w)) for c, w in widths.items() if c not in (" ", " ")}
    codes = sorted(ord(c) for c in units)
    ranges, cur = [], None
    for cp in codes:
        if cur and cp == cur[0] + len(cur[1]):
            cur[1].append(units[chr(cp)])
        elif cur and cp - (cur[0] + len(cur[1])) <= 8:  # 작은 틈은 0(모름)으로 메운다
            cur[1].extend([0] * (cp - (cur[0] + len(cur[1]))))
            cur[1].append(units[chr(cp)])
        else:
            cur = [cp, [units[chr(cp)]]]
            ranges.append(cur)
    return ranges


def main(src, dst):
    han = json.load(open(src, encoding="utf-8"))
    entries = [
        {"name": font, "bold": False, "em": 1000, "hangul": 970, "ranges": table(w)}
        for font, w in han.items()
    ]
    old = json.load(open(dst, encoding="utf-8"))
    names = {e["name"] for e in entries}
    merged = [e for e in old if e["name"] not in names] + entries
    json.dump(merged, open(dst, "w", encoding="utf-8"), ensure_ascii=False)
    for e in entries:
        print(e["name"], "구간", len(e["ranges"]), "글자", sum(len(r[1]) for r in e["ranges"]))
    print(f"{len(merged)}개 글꼴 → {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
