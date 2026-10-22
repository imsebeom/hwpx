"""실측 표(hft-metrics.json)의 함초롬바탕, 함초롬돋움에 e14, e15 에서 빠진 글자의 폭을 넣는다.

    python add_hft_glyph.py <hft-metrics.json>

・(U+30FB): 한/글 2024 PDF 에서 함초롬바탕 「가・가」 의 ・ 폭이 한글 음절과 같다(scratchpad mg 실험, 장평 100% 자간 0,
9.715pt 대 9.715pt). 맑은 고딕(파일에 ・ 없음)도 0.971em 으로 함초롬 대체 폭이다(lab e20). 엔진은 표에 없어 1em 으로 어림했다.
이 표는 파일에 없는 글자의 대체 폭(font-metrics.mjs hcrFallback)으로도 쓰인다.
"""

import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
ADD = {0x30FB: 970}


def main(dst):
    entries = json.load(open(dst, encoding="utf-8"))
    for e in entries:
        if e["name"] not in ("함초롬바탕", "함초롬돋움"):
            continue
        em = e.get("em") or 1000
        for code, w in ADD.items():
            w = round(w * em / 1000)
            for start, widths in e["ranges"]:
                if start <= code < start + len(widths):
                    widths[code - start] = w
                    break
            else:
                e["ranges"].append([code, [w]])
                e["ranges"].sort(key=lambda r: r[0])
            print(e["name"], hex(code), w)
    json.dump(entries, open(dst, "w", encoding="utf-8"), ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1])
