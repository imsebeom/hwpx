"""python exp/make_zone.py ../out/fresh/rt/d130.hwpx <출력 폴더> → hwpx_lab/measure.py

d130 머리 띠 표: 칸 (0,0)(colSpan 2)의 채우기를 빼고 셀 영역(bf 11, 끝 주소 0,0)만 남겨
한/글이 셀 영역 배경을 병합 칸 끝까지 칠하는지 본다. 띠 높이는 383 → 3000.

a: 셀 영역 끝 주소 (0,0) 그대로   b: 끝 주소 (0,1)로 대조   c: 셀 영역 없음(칸 채우기도 없음)
"""

import re
import sys
import zipfile
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
zin = zipfile.ZipFile(src)
parts = [(i.filename, i.compress_type, zin.read(i.filename)) for i in zin.infolist()]


def variant(name, end_col):
    with zipfile.ZipFile(out / f"z_{name}.hwpx", "w", zipfile.ZIP_DEFLATED) as z:
        for fname, ct, data in parts:
            if fname == "Contents/section0.xml":
                x = data.decode("utf-8")
                zone = '<hp:cellzone startRowAddr="0" startColAddr="0" endRowAddr="0" endColAddr="0" borderFillIDRef="11"/>'
                assert x.count(zone) == 1
                if end_col is None:
                    x = re.sub(
                        r"<hp:cellzoneList>.*?</hp:cellzoneList>",
                        "",
                        x,
                        count=1,
                        flags=re.S,
                    )
                else:
                    x = x.replace(
                        zone, zone.replace('endColAddr="0"', f'endColAddr="{end_col}"')
                    )
                cell = '<hp:cellAddr colAddr="0" rowAddr="0"/><hp:cellSpan colSpan="2" rowSpan="1"/><hp:cellSz width="47671" height="383"/>'
                assert x.count(cell) == 1
                i = x.index(cell)
                tc = x.rfind("<hp:tc ", 0, i)
                head = x[tc:i]
                head2 = re.sub(
                    r'borderFillIDRef="8"', 'borderFillIDRef="1"', head, count=1
                )
                assert head2 != head
                x = (
                    x[:tc]
                    + head2
                    + cell.replace('height="383"', 'height="3000"')
                    + x[i + len(cell) :]
                )
                data = x.encode("utf-8")
            z.writestr(zipfile.ZipInfo(fname), data, compress_type=ct)


variant("a", 0)
variant("b", 1)
variant("c", None)
print("ok")
