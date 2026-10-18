"""d010 글머리표 문단(문단 모양 72: 글머리표 1, 왼쪽 여백 1000, 들여쓰기 -616, 자동 내어쓰기)의 들여쓰기와 자동 내어쓰기를
바꾼 변형을 만든다. p8 글을 늘려 두 줄이 되게 하고, 한/글 PDF 에서 글머리, 첫 줄 글, 둘째 줄 글의 x 를 잰다.

    python exp/make_bulletindent.py ../out/oracle/d010.hwpx <출력 폴더>
"""

import re
import sys
import zipfile
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
zin = zipfile.ZipFile(src)
parts = [(i.filename, i.compress_type, zin.read(i.filename)) for i in zin.infolist()]
EXTRA = " 둘째 줄로 넘어가도록 덧붙인 글입니다. 둘째 줄로 넘어가도록 덧붙인 글입니다."
VARIANTS = []
for indent in (-1500, -616, 0, 500):
    for auto in (1, 0):
        VARIANTS.append((f"i{indent}_a{auto}", indent, auto))

for name, indent, auto in VARIANTS:
    with zipfile.ZipFile(out / f"{name}.hwpx", "w", zipfile.ZIP_DEFLATED) as z:
        for fname, ct, data in parts:
            if fname == "Contents/header.xml":
                s = data.decode("utf-8")
                m = re.search(r'<hh:paraPr id="72".*?</hh:paraPr>', s, re.S)
                pp = m.group(0)
                pp2 = re.sub(r'(<hc:intent value=")-?\d+(")', rf"\g<1>{indent}\2", pp)
                s = s.replace(pp, pp2)
                b = re.search(r'<hh:bullet id="1".*?</hh:bullet>', s, re.S).group(0)
                s = s.replace(b, b.replace('autoIndent="1"', f'autoIndent="{auto}"'))
                data = s.encode("utf-8")
            if fname == "Contents/section0.xml":
                s = data.decode("utf-8")
                key = "혁신 의지 고양 필요"
                assert s.count(key) == 1, s.count(key)
                s = s.replace(key, key + EXTRA)
                s = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", s, flags=re.S)
                data = s.encode("utf-8")
            z.writestr(zipfile.ZipInfo(fname), data, compress_type=ct)
print("ok", [v[0] for v in VARIANTS])
