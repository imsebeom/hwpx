"""Word 호환 정답본(d076, d133)에서 한 줄짜리 문단을 글자 모양 조합(글이 있는 run, 빈 run)별로 묶어
한/글 줄 높이(vertsize)와 기준선(baseline)을 단일 글꼴 규칙의 예측값과 나란히 둔다.

    python harvest_wordmix.py d076 d133

단일 규칙: lh = 크기 x hhea 비 x 1.3, 기준선 = ascender x 크기 + (lh - hhea 비 x 크기) / 2
"""

import collections
import os
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
from fontTools.ttLib import TTFont  # noqa: E402

FILES = {
    "맑은 고딕": "C:/Windows/Fonts/malgun.ttf",
    "Pretendard": "C:/Windows/Fonts/Pretendard-Regular.ttf",
}


def vm(face):
    f = FILES.get(face)
    if not f or not os.path.exists(f):
        return None
    t = TTFont(f, fontNumber=0)
    h = t["hhea"]
    u = t["head"].unitsPerEm
    return h.ascent / u, -h.descent / u, h.lineGap / u


def single(face, size):
    m = vm(face)
    if not m:
        return None
    ratio = sum(m)
    lh = size * ratio * 1.3
    return round(lh), round(m[0] * size + (lh - ratio * size) / 2)


for doc in sys.argv[1:]:
    z = zipfile.ZipFile(f"../out/oracle/{doc}.hwpx")
    h = z.read("Contents/header.xml").decode()
    faces = dict(
        re.findall(
            r'<hh:font id="(\d+)" face="([^"]+)"',
            re.search(r'<hh:fontface lang="HANGUL".*?</hh:fontface>', h, re.S).group(0),
        )
    )
    chars = {}
    for m in re.finditer(
        r'<hh:charPr id="(\d+)" height="(\d+)".*?</hh:charPr>', h, re.S
    ):
        chars[m.group(1)] = (
            faces.get(
                re.search(r'<hh:fontRef hangul="(\d+)"', m.group(0)).group(1), "?"
            ),
            int(m.group(2)),
        )
    stat = collections.Counter()
    for sec in sorted(
        n for n in z.namelist() if re.match(r"Contents/section\d+\.xml", n)
    ):
        s = z.read(sec).decode()
        for p in re.findall(r"<hp:p [^>]*>(?:(?!<hp:p ).)*?</hp:p>", s, re.S):
            segs = re.findall(r'vertsize="(\d+)" textheight="\d+" baseline="(\d+)"', p)
            if len(segs) != 1 or re.search(
                r"<hp:(tbl|pic|equation|container|rect|line)\b", p
            ):
                continue
            body = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", p, flags=re.S)
            text, empty = set(), set()
            for cid, inner in re.findall(
                r'<hp:run charPrIDRef="(\d+)"(?:/>()|>(.*?)</hp:run>)', body, re.S
            ) and [
                (a, c)
                for a, _, c in re.findall(
                    r'<hp:run charPrIDRef="(\d+)"(/>|>(.*?)</hp:run>)', body, re.S
                )
            ]:
                (text if re.search(r"<hp:t>[^<]", inner or "") else empty).add(
                    chars[cid]
                )
            empty -= text
            vs, bl = int(segs[0][0]), int(segs[0][1])
            stat[(tuple(sorted(text)), tuple(sorted(empty)), vs, bl)] += 1
    print("==", doc)
    for (text, empty, vs, bl), n in sorted(stat.items(), key=lambda kv: -kv[1]):
        if not text or (not empty and len(text) < 2):
            continue
        pred = {f"{f} {s}": single(f, s) for f, s in text + empty}
        print(f"{n:5}  글 {list(text)} 빈 {list(empty)}  한/글 {vs}/{bl}  단일 {pred}")
