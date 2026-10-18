"""새 정답본 사본(줄 배치 지움, out/fresh/in)의 문단 정렬을 모두 왼쪽으로 바꾼다. 한/글로 다시 저장해(measure.py) 양쪽 정렬로 늘어나지
않은 글자 위치(자연 폭)를 PDF 로 얻는다(exp/charwidth.py 가 엔진과 견준다).

    python exp/make_leftalign.py [<출력 폴더, 기본 ../out/left/in>]
"""

import re
import sys
import zipfile
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent.parent / "out"
dst = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT / "left" / "in"
dst.mkdir(parents=True, exist_ok=True)
n = 0
for f in sorted((OUT / "fresh" / "in").glob("*.hwpx")):
    zin = zipfile.ZipFile(f)
    with zipfile.ZipFile(dst / f.name, "w", zipfile.ZIP_DEFLATED) as z:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename == "Contents/header.xml":
                data = re.sub(
                    rb'horizontal="(JUSTIFY|DISTRIBUTE|DISTRIBUTE_SPACE)"',
                    b'horizontal="LEFT"',
                    data,
                )
            z.writestr(
                zipfile.ZipInfo(info.filename),
                data,
                compress_type=zipfile.ZIP_STORED
                if info.filename == "mimetype"
                else zipfile.ZIP_DEFLATED,
            )
    n += 1
print("ok", n, dst)
