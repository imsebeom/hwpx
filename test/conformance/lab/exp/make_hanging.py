"""d322 사본에서 문단 모양 60(칸 안 내어쓰기 문단)의 들여쓰기 값을 바꾼 변형을 만든다(한/글 실험).

    python exp/make_hanging.py

결과 폴더: %TEMP%/hanging/in/i<값>.hwpx. 한/글 재저장본에서 칸 1297 의 줄 시작을 읽어 내어쓰기를 지키는지 본다.
"""

import os
import re
import shutil
import zipfile

src = r"C:\Users\hccga\Desktop\code\.automation_and_skill\hwpx 에디터기반 에이전트스킬\test\conformance\out\oracle\d322.hwpx"
base = os.path.join(os.environ["TEMP"], "hanging")
shutil.rmtree(base, ignore_errors=True)
os.makedirs(os.path.join(base, "in"))
os.makedirs(os.path.join(base, "rt"))
z = zipfile.ZipFile(src)
entries = [(i, z.read(i.filename)) for i in z.infolist()]
header = next(d for i, d in entries if i.filename == "Contents/header.xml").decode(
    "utf-8"
)
m = re.search(r'<hh:paraPr id="60".*?</hh:paraPr>', header, re.S)
for v in [int(x) for x in os.environ.get("HANG_VALUES", "0,-1000,-2000,-3000,-3500,-4000,-4500,-5048").split(",")]:
    pp = m.group(0)
    # case 는 HwpUnitChar(값 그대로), default 는 2 배
    case = re.search(r"<hp:case\b.*?</hp:case>", pp, re.S).group(0)
    dflt = re.search(r"<hp:default>.*?</hp:default>", pp, re.S).group(0)
    case2 = re.sub(r'<hc:intent value="-?\d+"', f'<hc:intent value="{v}"', case)
    dflt2 = re.sub(r'<hc:intent value="-?\d+"', f'<hc:intent value="{v * 2}"', dflt)
    pp2 = pp.replace(case, case2).replace(dflt, dflt2)
    h2 = header.replace(pp, pp2)
    with zipfile.ZipFile(os.path.join(base, "in", f"i{abs(v):04d}.hwpx"), "w") as w:
        for info, data in entries:
            if info.filename == "Contents/header.xml":
                data = h2.encode("utf-8")
            w.writestr(
                info,
                data,
                compress_type=zipfile.ZIP_STORED
                if info.filename == "mimetype"
                else zipfile.ZIP_DEFLATED,
            )
print(sorted(os.listdir(os.path.join(base, "in"))))
