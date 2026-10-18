"""d322 사본(줄 배치 지움)에서 표 둘을 품은 p77 뒤 빈 문단 p78 에 글을 넣어, 둘째 표가 다음 쪽으로 갈 때 뒤 글이 어느 쪽에 오는지 본다.

    python exp/make_twofloat.py ../out/fresh/in/d322.hwpx <출력 폴더>

변형: one(p78 에 「따라오는글01」), many(p78 을 「따라오는글01」~「따라오는글40」 문단 40개로).
한/글 PDF 에서 「따라오는글」 의 쪽과 y 를 읽는다(read_twofloat.py).
"""

import sys
import zipfile
from pathlib import Path

from lxml import etree

HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
src, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
zin = zipfile.ZipFile(src)
parts = [(i.filename, i.compress_type, zin.read(i.filename)) for i in zin.infolist()]


def variant(name, count):
    with zipfile.ZipFile(out / f"t_{name}.hwpx", "w", zipfile.ZIP_DEFLATED) as z:
        for fname, ct, data in parts:
            if fname == "Contents/section0.xml":
                root = etree.fromstring(data)
                ps = [p for p in root if p.tag == f"{HP}p"]
                p78 = ps[78]
                run = p78.find(f"{HP}run")
                t = etree.SubElement(run, f"{HP}t")
                t.text = "따라오는글01"
                idx = list(root).index(p78)
                for k in range(2, count + 1):
                    clone = etree.fromstring(etree.tostring(p78))
                    clone.find(f"{HP}run/{HP}t").text = f"따라오는글{k:02d}"
                    root.insert(idx + k - 1, clone)
                data = etree.tostring(
                    root, xml_declaration=True, encoding="UTF-8", standalone=True
                )
            z.writestr(zipfile.ZipInfo(fname), data, compress_type=ct)


variant("one", 1)
variant("many", 40)
print("ok")
