"""회귀 코퍼스 목록에서 이름이 맞는 파일을 <대상 폴더>/in/w<i>.hwpx 로 베끼고, 줄 배치를 지운 사본(<폴더>/w<i>_s.hwpx)도 만든다.

python copy_reg.py <대상 폴더> <파일 이름>...
"""

import os
import re
import shutil
import sys
import zipfile

LIST = r"C:/Users/hccga/Desktop/code/.automation_and_skill/hwpx 에디터기반 에이전트스킬/test/linebreak/results/reg_corpus_1014.txt"
base = sys.argv[1]
names = sys.argv[2:]
shutil.rmtree(base, ignore_errors=True)
os.makedirs(os.path.join(base, "in"))
os.makedirs(os.path.join(base, "rt"))
paths = [line.strip() for line in open(LIST, encoding="utf-8") if line.strip()]
for i, name in enumerate(names):
    hit = next(p for p in paths if os.path.basename(p.replace("\\", "/")) == name)
    dst = os.path.join(base, "in", f"w{i}.hwpx")
    shutil.copyfile(hit, dst)
    z = zipfile.ZipFile(dst)
    ents = [(info, z.read(info.filename)) for info in z.infolist()]
    with zipfile.ZipFile(os.path.join(base, f"w{i}_s.hwpx"), "w") as w:
        for info, data in ents:
            if re.match(r"Contents/section\d+\.xml$", info.filename):
                data = re.sub(
                    r"<hp:linesegarray>.*?</hp:linesegarray>",
                    "",
                    data.decode("utf-8"),
                    flags=re.S,
                ).encode("utf-8")
            w.writestr(info, data)
    print(i, hit)
