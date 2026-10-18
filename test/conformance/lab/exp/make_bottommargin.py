"""문서의 아래 여백(margin bottom)을 50 HU 씩 줄인 변형을 만든다(본문이 그만큼 길어진다).

    python make_bottommargin.py <원본 hwpx> <출력 폴더> [단계 수]

칸 안에서 쪽을 넘길 때 1쪽에 담는 줄 수가 아래 여백 몇 HU 에서 바뀌는지 보아 쪽 끝 판정의 남는 자리를 잰다.
"""

import os
import re
import shutil
import sys
import zipfile

src, base = sys.argv[1], sys.argv[2]
steps = int(sys.argv[3]) if len(sys.argv) > 3 else 19
shutil.rmtree(base, ignore_errors=True)
os.makedirs(os.path.join(base, "in"))
os.makedirs(os.path.join(base, "rt"))
z = zipfile.ZipFile(src)
entries = [(i, z.read(i.filename)) for i in z.infolist()]
sec = next(d for i, d in entries if i.filename == "Contents/section0.xml").decode(
    "utf-8"
)
m = re.search(r'(<hp:margin [^>]*bottom=")(\d+)(")', sec)
bottom = int(m.group(2))
for k in range(steps):
    b = bottom - 50 * k
    s = sec[: m.start()] + m.group(1) + str(b) + m.group(3) + sec[m.end() :]
    with zipfile.ZipFile(os.path.join(base, "in", f"b{50 * k:04d}.hwpx"), "w") as w:
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
print(bottom, steps)
