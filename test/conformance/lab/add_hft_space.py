"""실측 표(hft-metrics.json)에 「글꼴에 어울리는 빈칸」을 켰을 때의 빈칸 폭(lab e25)을 넣는다.

    python add_hft_space.py <e25_space.json> <hft-metrics.json>

꺼져 있을 때는 엔진이 글자 크기의 절반을 쓰고(e1, e24), 켜져 있을 때 이 값을 쓴다(use-font-space 패치의 metricFontSpace).
"""

import json
import sys

sys.stdout.reconfigure(encoding="utf-8")


def main(src, dst):
    space = json.load(open(src, encoding="utf-8"))
    entries = json.load(open(dst, encoding="utf-8"))
    for e in entries:
        w = space.get(e["name"])
        if not w:
            continue
        w = round(w * (e.get("em") or 1000) / 1000)
        ranges = e["ranges"]
        if ranges and ranges[0][0] == 0x20:
            ranges[0][1][0] = w
        elif ranges and ranges[0][0] == 0x21:
            ranges[0] = [0x20, [w] + ranges[0][1]]
        else:
            ranges.insert(0, [0x20, [w]])
        print(e["name"], "빈칸", w)
    json.dump(entries, open(dst, "w", encoding="utf-8"), ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
