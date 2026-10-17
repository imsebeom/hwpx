"""pdfadv.py(한/글) 와 rhwpadv.mjs(rhwp) 결과를 글자별로 맞대어 차이 나는 글자를 찍는다.

    python cmpadv.py <한글.json> <rhwp.json> [문턱 pt=0.1]

한/글 PDF 좌표는 글자 크기 대비 0.9955 배로 나온다(10pt 한글 전각이 9.955pt) — 그만큼 되돌려 비교한다.
rhwp 커서 x 는 0.1px(0.075pt) 눈금이라 문턱은 그보다 크게 둔다.
"""

import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
PDF_SCALE = 0.9955


def main():
    han = json.load(open(sys.argv[1], encoding="utf-8"))
    rh = json.load(open(sys.argv[2], encoding="utf-8"))
    th = float(sys.argv[3]) if len(sys.argv) > 3 else 0.1
    for name in sorted(han):
        if name not in rh:
            continue
        a, b = han[name]["adv"], rh[name]["adv"]
        diffs = []
        for ch, hv in a.items():
            if ch not in b or b[ch] is None:
                continue
            d = b[ch] - hv / PDF_SCALE
            if abs(d) > th:
                diffs.append(f"{ch}:{hv / PDF_SCALE:.2f}/{b[ch]:.2f}")
        print(f"{name} 다른 글자 {len(diffs)}/{len(a)}  " + " ".join(diffs[:40]))


if __name__ == "__main__":
    main()
