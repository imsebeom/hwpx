import os
import re
import shutil
import zipfile

src = r"C:\Users\hccga\Desktop\code\.automation_and_skill\hwpx 에디터기반 에이전트스킬\test\conformance\out\oracle\d193.hwpx"
out = os.path.join(os.environ["TEMP"], "push", "in")
shutil.rmtree(os.path.join(os.environ["TEMP"], "push"), ignore_errors=True)
os.makedirs(out)
os.makedirs(os.path.join(os.environ["TEMP"], "push", "rt"))
z = zipfile.ZipFile(src)
entries = [(i, z.read(i.filename)) for i in z.infolist()]
sec = next(d for i, d in entries if i.filename == "Contents/section0.xml").decode(
    "utf-8"
)
TID = "1210124188"
ti = sec.find(f'<hp:tbl id="{TID}"')
p57 = sec.rfind("<hp:p ", 0, ti)
# 빈 문단 하나(줄 배치 없음, 글자 모양 0, 문단 모양 0)
EMPTY = '<hp:p id="2147483648" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="0"/></hp:p>'
# 앞의 빈 문단을 그대로 베낀다: p57 바로 앞 문단
prev_start = sec.rfind("<hp:p ", 0, p57 - 1)
prev = sec[prev_start:p57]
print("prev para len", len(prev), prev[:160])


def variant(k):
    s = sec[:p57] + EMPTY * k + sec[p57:]
    return s


for k in (0, 1, 2, 3, 4):
    with zipfile.ZipFile(os.path.join(out, f"k{k}.hwpx"), "w") as w:
        for info, data in entries:
            if info.filename == "Contents/section0.xml":
                data = variant(k).encode("utf-8")
            w.writestr(
                info,
                data,
                compress_type=zipfile.ZIP_STORED
                if info.filename == "mimetype"
                else zipfile.ZIP_DEFLATED,
            )
print(sorted(os.listdir(out)))
