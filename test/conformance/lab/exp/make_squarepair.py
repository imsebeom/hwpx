"""d268 둘째 구역 p31 의 어울림 차트 둘(ole)을 바꾼 변형. 한/글 PDF 에서 다음 문단 p32~ 가 차트 옆으로 흐르는지, 아래로 가는지 본다.

    python exp/make_squarepair.py ../out/oracle/d268.hwpx <출력 폴더>

변형: orig(나란히 단 폭을 덮음), one(오른쪽 차트를 지움 — 반 폭), gap5k, gap10k, gap20k(오른쪽 차트를 그만큼 줄여 가운데 틈)
"""

import re
import sys
import zipfile
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
zin = zipfile.ZipFile(src)
parts = [(i.filename, i.compress_type, zin.read(i.filename)) for i in zin.infolist()]
sec = next(d for f, _, d in parts if f == "Contents/section1.xml").decode("utf-8")

# 오른쪽 차트: horzOffset="23491" 인 hp:switch(ole + chart) 덩어리
m = re.search(
    r'<hp:switch>(?:(?!<hp:switch>).)*?horzOffset="23491"(?:(?!</hp:switch>).)*</hp:switch>',
    sec,
    re.S,
)
assert m, "오른쪽 차트를 못 찾음"
right = m.group(0)


def shrink(block, gap):
    # 오른쪽 차트를 gap 만큼 오른쪽으로 옮기고 폭을 줄인다(오른쪽 끝은 그대로)
    b = block.replace('horzOffset="23491"', f'horzOffset="{23491 + gap}"')
    return re.sub(r'(<hp:sz width=")24699(")', rf"\g<1>{24699 - gap}\2", b)


VARIANTS = {
    "orig": sec,
    "one": sec.replace(right, ""),
    "gap5k": sec.replace(right, shrink(right, 5000)),
    "gap10k": sec.replace(right, shrink(right, 10000)),
    "gap20k": sec.replace(right, shrink(right, 20000)),
}
for name, s in VARIANTS.items():
    s = (
        re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", s, flags=re.S)
        if name != "orig"
        else s
    )
    with zipfile.ZipFile(out / f"sq_{name}.hwpx", "w", zipfile.ZIP_DEFLATED) as z:
        for fname, ct, data in parts:
            if fname == "Contents/section1.xml":
                data = s.encode("utf-8")
            z.writestr(zipfile.ZipInfo(fname), data, compress_type=ct)
print("ok", list(VARIANTS), "오른쪽 차트 덩어리", len(right))
