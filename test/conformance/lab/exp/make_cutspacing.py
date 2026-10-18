"""d243 의 둘째 표(CELL 쪽 나눔) 세로 위치(vertOffset 438)를 50 HU 씩 바꾼 변형을 만든다.

    python make_cutspacing.py        -> %TEMP%/cutsp/in/o<offset>.hwpx

행 2 의 교사 칸(4줄 뒤에 줄이 더 있음)과 학생 칸(4줄이 칸의 전부)이 1쪽에 담는 줄 수를 offset 마다 본다.
쪽 끝에서 칸 안을 자를 때 마지막으로 담는 줄의 뒤 줄 간격(600)을 한/글이 세면 교사 칸이 학생 칸보다 600 HU 먼저
4번째 줄을 넘기고, 세지 않으면 두 칸이 같은 offset 에서 넘긴다.
"""

import os
import shutil
import zipfile

src = os.path.join(os.path.dirname(__file__), "..", "..", "out", "oracle", "d243.hwpx")
base = os.path.join(os.environ["TEMP"], "cutsp")
shutil.rmtree(base, ignore_errors=True)
os.makedirs(os.path.join(base, "in"))
os.makedirs(os.path.join(base, "rt"))
z = zipfile.ZipFile(src)
entries = [(i, z.read(i.filename)) for i in z.infolist()]
sec = next(d for i, d in entries if i.filename == "Contents/section0.xml").decode(
    "utf-8"
)
anchor = 'id="1748696691"'
i = sec.find(anchor)
assert i > 0 and sec.count(anchor) == 1
j = sec.find('vertOffset="438"', i)
assert 0 < j < i + 3000
for off in list(range(438, 498, 10)) + list(range(738, 798, 10)):
    s = sec[:j] + f'vertOffset="{off}"' + sec[j + len('vertOffset="438"') :]
    with zipfile.ZipFile(os.path.join(base, "in", f"o{off:04d}.hwpx"), "w") as w:
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
