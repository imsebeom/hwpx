"""Word 호환(compatibleDocument targetProgram=MS_WORD) 정답본에서 줄 높이(vertsize)를 글꼴, 글자 크기, 줄 간격별로 모은다.

    python harvest_wordcompat.py d076 d133

한 줄짜리 본문 문단만 보고(여러 글자 모양이면 가장 큰 크기), 글꼴 파일의 hhea 줄 높이((ascent+descent+lineGap)/upm)와 나란히 둔다.
"""

import collections
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
from fontTools.ttLib import TTFont  # noqa: E402

FONT_FILES = {
    "맑은 고딕": "malgun.ttf",
    "한컴바탕": None,
    "Pretendard": None,
    "Arial": "arial.ttf",
    "Times New Roman": "times.ttf",
    "바탕": "batang.ttc",
    "굴림": "gulim.ttc",
}


def hhea_ratio(face):
    f = FONT_FILES.get(face)
    if not f:
        return None
    try:
        t = TTFont(f"C:/Windows/Fonts/{f}", fontNumber=0)
        h = t["hhea"]
        return round((h.ascent - h.descent + h.lineGap) / t["head"].unitsPerEm, 4)
    except Exception:
        return None


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
            int(m.group(2)),
            faces.get(
                re.search(r'<hh:fontRef hangul="(\d+)"', m.group(0)).group(1), "?"
            ),
        )
    paras = {}
    for m in re.finditer(r'<hh:paraPr id="(\d+)".*?</hh:paraPr>', h, re.S):
        ls = re.search(r'<hh:lineSpacing type="(\w+)" value="(-?\d+)"', m.group(0))
        paras[m.group(1)] = (ls.group(1), int(ls.group(2)))
    stat = collections.Counter()
    for n in sorted(
        x for x in z.namelist() if re.match(r"Contents/section\d+\.xml$", x)
    ):
        x = z.read(n).decode()
        for m in re.finditer(r"<hp:p\b[^>]*>(?:(?!<hp:p\b).)*?</hp:p>", x, re.S):
            p = m.group(0)
            segs = re.findall(
                r'vertsize="(\d+)" textheight="(\d+)" baseline="(\d+)" spacing="(-?\d+)"',
                p,
            )
            if len(segs) != 1 or "<hp:tbl" in p or "<hp:pic" in p:
                continue
            cps = [
                chars[c] for c in re.findall(r'charPrIDRef="(\d+)"', p) if c in chars
            ]
            if not cps:
                continue
            fs, face = max(cps)
            ls = paras.get(re.search(r'paraPrIDRef="(\d+)"', p).group(1), ("?", 0))
            vs, th, bl, sp = (int(v) for v in segs[0])
            stat[(face, fs, ls, vs, bl, sp)] += 1
    print(f"== {doc}")
    for (face, fs, ls, vs, bl, sp), k in sorted(stat.items(), key=lambda kv: -kv[1])[
        :14
    ]:
        print(
            f"  {k:3d}  {face} {fs} {ls[0]} {ls[1]}  vertsize {vs} ({vs / fs:.4f}배) baseline {bl} spacing {sp}  글꼴 hhea {hhea_ratio(face)}"
        )
