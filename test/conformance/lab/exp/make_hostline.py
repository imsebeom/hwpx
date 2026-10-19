"""새 정답본 입력 d034(줄 배치 지움)의 p65(글 「가. 목적」 + 오른쪽 자리 차지 표, 오프셋 196, 줄 1300 + 간격 1040)에서 표 세로 오프셋을
바꿔, 한/글이 글줄을 표 위에 두는지 아래에 두는지 본다.

    python exp/make_hostline.py ../out/fresh/in/d034.hwpx <출력 폴더> [오프셋,오프셋,...]

변형 o<오프셋>: 0, 196, 1000, 1900, 2300, 2400, 3000, 5000. 한/글 측정 뒤 rt 의 p65 줄 vpos 와 p66 vpos 를 읽는다(exp/read_hostline.py).
"""

import sys
import zipfile
from pathlib import Path

from lxml import etree

HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
PI = 65
src, out = Path(sys.argv[1]), Path(sys.argv[2])
OFFS = [int(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else [0, 196, 1000, 1900, 2300, 2400, 3000, 5000]
out.mkdir(parents=True, exist_ok=True)
zin = zipfile.ZipFile(src)
parts = [(i.filename, i.compress_type, zin.read(i.filename)) for i in zin.infolist()]

for off in OFFS:
    with zipfile.ZipFile(out / f"o{off}.hwpx", "w", zipfile.ZIP_DEFLATED) as z:
        for fname, ct, data in parts:
            if fname == "Contents/section0.xml":
                root = etree.fromstring(data)
                ps = [p for p in root if p.tag == f"{HP}p"]
                ps[PI].find(f"{HP}run/{HP}tbl/{HP}pos").set("vertOffset", str(off))
                data = etree.tostring(
                    root, xml_declaration=True, encoding="UTF-8", standalone=True
                )
            z.writestr(zipfile.ZipInfo(fname), data, compress_type=ct)
print("ok")
