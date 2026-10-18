"""d243 둘째 표의 바깥 여백 아래(141)를 바꾸고 세로 위치(vertOffset)를 50 HU 씩 옮긴 변형을 만든다.

    python make_outmargin243.py        -> %TEMP%/om243/in/b<여백>_o<offset>.hwpx

교사 칸이 4번째 줄을 넘기는 offset 이 여백 아래 변화량의 몇 배로 옮겨 가는지 보아, 쪽 끝 칸 자르기가 바깥 여백
아래를 몇 번 남기는지 잰다(원본 여백 141 에서는 offset 768~778 사이).
"""

import os
import shutil
import zipfile

src = os.path.join(os.path.dirname(__file__), "..", "..", "out", "oracle", "d243.hwpx")
base = os.path.join(os.environ["TEMP"], "om243")
shutil.rmtree(base, ignore_errors=True)
os.makedirs(os.path.join(base, "in"))
os.makedirs(os.path.join(base, "rt"))
z = zipfile.ZipFile(src)
entries = [(i, z.read(i.filename)) for i in z.infolist()]
sec = next(d for i, d in entries if i.filename == "Contents/section0.xml").decode(
    "utf-8"
)
i = sec.find('id="1748696691"')
j = sec.find('vertOffset="438"', i)
k = sec.find('<hp:outMargin left="141" right="141" top="141" bottom="141"/>', i)
assert 0 < j < k < i + 3000
for ob in (0, 283, 425):
    for off in range(150, 1101, 50):
        s = (
            sec[:j]
            + f'vertOffset="{off}"'
            + sec[j + len('vertOffset="438"') : k]
            + f'<hp:outMargin left="141" right="141" top="141" bottom="{ob}"/>'
            + sec[
                k
                + len('<hp:outMargin left="141" right="141" top="141" bottom="141"/>') :
            ]
        )
        with zipfile.ZipFile(
            os.path.join(base, "in", f"b{ob:03d}_o{off:04d}.hwpx"), "w"
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
print(len(os.listdir(os.path.join(base, "in"))))
