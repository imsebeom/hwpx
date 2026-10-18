"""issue1949 표본에서 쪽 끝 칸 자르기가 남기는 자리가 표 여백에서 오는지 가리는 변형을 만든다.

    python make_reserve1949.py <원본 hwpx> <출력 폴더>

설정: base(그대로), out0(표 바깥 여백 아래 283 -> 0), in0(표 안쪽 여백 아래 141 -> 0).
각 설정마다 아래 여백을 0, 100, 200, 250, 300, 400 HU 줄인다. 1쪽 38번째 줄이 들어오는 아래 여백 감소량이
설정에 따라 얼마나 옮겨 가는지 본다.
"""

import os
import re
import shutil
import sys
import zipfile

src, base = sys.argv[1], sys.argv[2]
shutil.rmtree(base, ignore_errors=True)
os.makedirs(os.path.join(base, "in"))
os.makedirs(os.path.join(base, "rt"))
z = zipfile.ZipFile(src)
entries = [(i, z.read(i.filename)) for i in z.infolist()]
sec = next(d for i, d in entries if i.filename == "Contents/section0.xml").decode(
    "utf-8"
)
t = sec.find('<hp:tbl id="1748807031"')
assert t > 0
om = re.compile(r'<hp:outMargin left="283" right="283" top="283" bottom="283"/>')
im = re.compile(r'<hp:inMargin left="141" right="141" top="141" bottom="141"/>')


def first_after(rx, s, pos):
    m = rx.search(s, pos)
    assert m and m.start() < pos + 2000, rx.pattern
    return m


configs = {
    "base": sec,
    "out0": (
        lambda m: (
            sec[: m.start()]
            + m.group(0).replace('bottom="283"', 'bottom="0"')
            + sec[m.end() :]
        )
    )(first_after(om, sec, t)),
    "in0": (
        lambda m: (
            sec[: m.start()]
            + m.group(0).replace('bottom="141"', 'bottom="0"')
            + sec[m.end() :]
        )
    )(first_after(im, sec, t)),
}
for name, s0 in configs.items():
    m = re.search(r'(<hp:margin [^>]*bottom=")(\d+)(")', s0)
    bottom = int(m.group(2))
    for d in (0, 100, 200, 250, 300, 400):
        s = s0[: m.start()] + m.group(1) + str(bottom - d) + m.group(3) + s0[m.end() :]
        with zipfile.ZipFile(
            os.path.join(base, "in", f"{name}_{d:03d}.hwpx"), "w"
        ) as w:
            for info, data in entries:
                if info.filename == "Contents/section0.xml":
                    data = s.encode("utf-8")
                w.writestr(
                    info,
                    data,
                    compress_type=zipfile.ZIP_STORED
                    if info.filename == "mimetype"
                    else zipfile.ZIP_DEFLATED,
                )
print(sorted(os.listdir(os.path.join(base, "in"))))
