"""issue1949 표본에 엔진 시험(#2214, #2424)과 같은 편집을 XML 로 해 둔 사본을 만든다.

    python make_edit1949.py <원본 hwpx> <출력 hwpx>

시험은 표(문단 0 의 조판 부호 2) 행 2 칸의 문단 5, 글자 위치 130 에 "1" 을 61 번 넣는다. 같은 글을 그 자리에 넣고
줄 배치(linesegarray)는 그대로 둔다(한/글은 열 때 다시 조판한다).
"""

import re
import sys
import zipfile

src, dst = sys.argv[1], sys.argv[2]
z = zipfile.ZipFile(src)
entries = [(i, z.read(i.filename)) for i in z.infolist()]
sec = next(d for i, d in entries if i.filename == "Contents/section0.xml").decode(
    "utf-8"
)
t = sec.find('<hp:tbl id="1748807031"')
tcs = [m.start() for m in re.finditer(r"<hp:tc\b", sec[t:])]
# 행 2 칸 = 이 표의 셋째 tc (바깥 표는 3x1)
c = t + tcs[2]
sub = sec.find("<hp:subList", c)
pos = sec.find(">", sub) + 1
# subList 바로 아래 문단만 센다(중첩 subList 안은 건너뛴다)
depth, k, p5 = 0, 0, None
for m in re.finditer(r"<(/?)hp:(p|subList)\b[^>]*?(/?)>", sec[pos:]):
    close, selfc = m.group(1) == "/", m.group(3) == "/"
    if m.group(2) == "subList":
        if selfc:
            continue
        if close and depth == 0:
            break
        depth += -1 if close else 1
        continue
    if depth or close or selfc:
        continue
    if k == 5:
        p5 = pos + m.start()
        break
    k += 1
assert p5
p_end = sec.find("</hp:p>", p5)
body = sec[p5:p_end]
# 글자 위치 130 을 품은 <hp:t> 를 찾는다(조판 부호는 글자 수에 넣지 않는 단순 셈: 이 문단은 글만 있다)
off = 0
for m in re.finditer(r"<hp:t>([^<]*)</hp:t>", body):
    n = len(m.group(1))
    if off + n >= 130:
        at = p5 + m.start(1) + (130 - off)
        sec = sec[:at] + "1" * 61 + sec[at:]
        break
    off += n
else:
    sys.exit("위치 130 없음")
print("문단 5 글:", re.sub(r"<[^>]+>", "", body)[:60], "...")
with zipfile.ZipFile(dst, "w") as w:
    for info, data in entries:
        if info.filename == "Contents/section0.xml":
            data = sec.encode("utf-8")
        w.writestr(
            info,
            data,
            compress_type=zipfile.ZIP_STORED
            if info.filename == "mimetype"
            else zipfile.ZIP_DEFLATED,
        )
