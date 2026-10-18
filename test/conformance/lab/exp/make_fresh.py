"""정답본에서 줄 배치를 지운 사본을 만든다. 한/글로 열어 다시 저장하면(measure.py) 한/글이 처음부터 조판한 줄 배치(새 정답본)를 얻는다.

    python exp/make_fresh.py [<출력 폴더, 기본 ../out/fresh/in>]

까닭(2026-10-19, d268 p121): 한/글은 저장된 줄 배치를 믿고 다시 조판하지 않는다. 정답본 d268 의 p121 은 한 줄로 저장돼 있지만
줄 배치를 지운 사본을 한/글이 조판하면 엔진과 똑같이 textpos 43 에서 꺾는다. nativescore 는 줄 배치를 지워 엔진이 처음부터
조판하게 하므로, 견줄 대상도 한/글이 처음부터 조판한 줄 배치여야 한다.
"""

import re
import sys
import zipfile
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent.parent / "out"
dst = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT / "fresh" / "in"
dst.mkdir(parents=True, exist_ok=True)
SEG = re.compile(r"<hp:linesegarray>.*?</hp:linesegarray>", re.S)
n = 0
for f in sorted((OUT / "oracle").glob("*.hwpx")):
    zin = zipfile.ZipFile(f)
    with zipfile.ZipFile(dst / f.name, "w", zipfile.ZIP_DEFLATED) as z:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if re.match(r"Contents/section\d+\.xml", info.filename):
                data = SEG.sub("", data.decode("utf-8")).encode("utf-8")
            z.writestr(
                zipfile.ZipInfo(info.filename),
                data,
                compress_type=zipfile.ZIP_STORED
                if info.filename == "mimetype"
                else zipfile.ZIP_DEFLATED,
            )
    n += 1
print("ok", n, dst)
