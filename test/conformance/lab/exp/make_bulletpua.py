"""d010 사본의 글머리표 글자(bullet id=1)만 바꾼 변형을 만든다. 한/글 PDF 에서 글머리 뒤 첫 글자 x 를 견준다.

    python exp/make_bulletpua.py ../out/oracle/d010.hwpx <출력 폴더>

변형: pua(원본 U+F0A3, Wingdings 기호 자리), pua2(U+F09F), circle(U+25CB ○), ascii(-), latin1(U+00B7 ·)
"""

import sys
import zipfile
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
zin = zipfile.ZipFile(src)
parts = [(i.filename, i.compress_type, zin.read(i.filename)) for i in zin.infolist()]
VARIANTS = {
    "pua": "",
    "pua2": "",
    "circle": "○",
    "ascii": "-",
    "latin1": "·",
    "sect": "§",
    "times": "×",
    "bull": "•",
    "endash": "–",
    "arrow": "→",
    "ring": "°",
    "square": "■",
}
for name, ch in VARIANTS.items():
    with zipfile.ZipFile(out / f"b_{name}.hwpx", "w", zipfile.ZIP_DEFLATED) as z:
        for fname, ct, data in parts:
            if fname == "Contents/header.xml":
                s = data.decode("utf-8")
                old = '<hh:bullet id="1" char=""'
                assert s.count(old) == 1, s.count(old)
                s = s.replace(old, f'<hh:bullet id="1" char="{ch}"')
                data = s.encode("utf-8")
            z.writestr(zipfile.ZipInfo(fname), data, compress_type=ct)
print("ok", list(VARIANTS))
