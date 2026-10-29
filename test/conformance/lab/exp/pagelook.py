"""쪽마다 생김새 대조: 엔진 SVG 와 한/글 PDF 의 글줄(빈칸 뺀 글)을 짝지어, 한/글 쪽을 엔진 좌표로 옮긴 뒤 글줄 y 차이를 잰다.

    python pagelook.py <엔진 svg 폴더(0.svg…)> <한글.pdf> [--png <폴더>]

한/글 PDF 는 인쇄 설정에 따라 쪽 전체가 축소, 이동되어 찍히므로(이 보고서는 약 0.79배) 쪽마다 짝지은 글줄로 y = a*y' + b 를 맞춘다.
쪽마다 「짝지은 줄 수 / 2px 넘게 다른 줄 수 / 가장 큰 차이」, 짝 못 지은 글줄 수를 찍는다. --png 이면 나란히 놓은 그림을 만든다.
"""

import glob
import os
import re
import sys

import pymupdf

sys.stdout.reconfigure(encoding="utf-8")


SCALE = float(os.environ.get("PAGELOOK_SCALE", "1.2705"))


def lines_of(page, k):
    out = []
    for b in page.get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            t = re.sub(r"\s+", "", "".join(s["text"] for s in ln["spans"]))
            if len(t) >= 4:
                # 글줄 상자 아래 끝은 글꼴 descent 에 따라 달라진다 — 첫 조각의 기준선(origin)을 쓴다
                out.append((t, ln["spans"][0]["origin"][1] * k))
    return out


def main():
    svgdir, pdf = sys.argv[1], sys.argv[2]
    png = sys.argv[sys.argv.index("--png") + 1] if "--png" in sys.argv else None
    if png:
        os.makedirs(png, exist_ok=True)
    hp = pymupdf.open(pdf)
    svgs = sorted(
        glob.glob(os.path.join(svgdir, "*.svg")),
        key=lambda p: int(os.path.basename(p)[:-4]),
    )
    print(f"엔진 {len(svgs)}쪽, 한글 {len(hp)}쪽")
    for i in range(max(len(svgs), len(hp))):
        if i >= len(svgs) or i >= len(hp):
            print(i + 1, "한쪽에만 있음")
            continue
        ep = pymupdf.open(svgs[i])[0]
        e = lines_of(ep, 1.0)
        h = lines_of(hp[i], ep.rect.height / hp[i].rect.height)

        # 같은 글줄(앞 8자) 짝짓기
        # 쪽에 한 번만 나오는 글줄(전체 글)끼리만 짝짓는다(「활동결과물」처럼 되풀이되는 글은 엉뚱하게 짝지어진다)
        def uniq(rows):
            cnt = {}
            for t, _ in rows:
                cnt[t] = cnt.get(t, 0) + 1
            return {t: y for t, y in rows if cnt[t] == 1}

        eu, hu = uniq(e), uniq(h)
        pairs = [(eu[t], hu[t], t) for t in eu if t in hu]
        if len(pairs) < 3:
            print(i + 1, f"짝 {len(pairs)} (비교 불가) 엔진줄 {len(e)} 한글줄 {len(h)}")
            continue
        # 배율은 인쇄 축소로 쪽마다 같다(SCALE). 위치만 중앙값으로 맞춘다
        offs = sorted(p[0] - SCALE * p[1] for p in pairs)
        b = offs[len(offs) // 2]
        d = [(p[0] - (SCALE * p[1] + b), p[2]) for p in pairs]
        bad = [x for x in d if abs(x[0]) > 2]
        worst = max(d, key=lambda x: abs(x[0]))
        print(
            i + 1,
            f"짝 {len(pairs)}/{len(e)}  2px넘음 {len(bad)}  최대 {worst[0]:+.1f}px 「{worst[1][:14]}」  못짝 엔진 {len(e) - len(pairs)} 한글 {len(h) - len(pairs)}",
        )
        if png:
            ep.get_pixmap(dpi=40).save(os.path.join(png, f"{i + 1:02d}_e.png"))
            hp[i].get_pixmap(dpi=40).save(os.path.join(png, f"{i + 1:02d}_h.png"))


if __name__ == "__main__":
    main()
