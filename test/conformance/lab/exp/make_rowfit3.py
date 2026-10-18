"""쪽번호시험(32px 행 CELL 표) 앞에 얇은 빈 문단(글자 크기 1pt) k 개를 넣어 1쪽 끝 남은 자리를 조금씩 줄인 변형을 만든다."""

import os
import re
import shutil
import zipfile

src = os.path.join(os.environ["TEMP"], "rg9", "in", "v2.hwpx")
base = os.path.join(os.environ["TEMP"], "rowfit3")
shutil.rmtree(base, ignore_errors=True)
os.makedirs(os.path.join(base, "in"))
os.makedirs(os.path.join(base, "rt"))
z = zipfile.ZipFile(src)
entries = [(i, z.read(i.filename)) for i in z.infolist()]
header = next(d for i, d in entries if i.filename == "Contents/header.xml").decode(
    "utf-8"
)
sec = next(d for i, d in entries if i.filename == "Contents/section0.xml").decode(
    "utf-8"
)

# 글자 모양 0 을 베껴 크기 100(1pt) 짜리를 새로 만든다
m = re.search(r'<hh:charPr id="0"[^>]*>.*?</hh:charPr>', header, re.S)
ids = [int(x) for x in re.findall(r'<hh:charPr id="(\d+)"', header)]
new_id = max(ids) + 1
cp = re.sub(r'id="0"', f'id="{new_id}"', m.group(0), count=1)
cp = re.sub(r'height="\d+"', 'height="100"', cp, count=1)
header2 = header.replace("</hh:charProperties>", cp + "</hh:charProperties>")
cnt = re.search(r'<hh:charProperties itemCnt="(\d+)"', header2)
header2 = header2.replace(
    cnt.group(0), f'<hh:charProperties itemCnt="{int(cnt.group(1)) + 1}"'
)
# 문단 모양: 줄 간격 100% 로 고정한 새 문단 모양
pm = re.search(r'<hh:paraPr id="0"[^>]*>.*?</hh:paraPr>', header2, re.S)
pids = [int(x) for x in re.findall(r'<hh:paraPr id="(\d+)"', header2)]
new_pid = max(pids) + 1
pp = re.sub(r'id="0"', f'id="{new_pid}"', pm.group(0), count=1)
pp = re.sub(
    r'<hh:lineSpacing type="\w+" value="\d+"',
    '<hh:lineSpacing type="PERCENT" value="100"',
    pp,
)
pp = re.sub(r'<hc:(prev|next) value="-?\d+"', r'<hc:\1 value="0"', pp)
header2 = header2.replace("</hh:paraProperties>", pp + "</hh:paraProperties>")
pcnt = re.search(r'<hh:paraProperties itemCnt="(\d+)"', header2)
header2 = header2.replace(
    pcnt.group(0), f'<hh:paraProperties itemCnt="{int(pcnt.group(1)) + 1}"'
)
print("charPr", new_id, "paraPr", new_pid)

# 첫 문단(구역 정의가 든 문단) 뒤에 넣는다
first_end = sec.find("</hp:p>") + len("</hp:p>")
# 셋째 문단(빈 문단 p2)을 뺀다: 둘째 문단 끝 뒤부터 셋째 문단 끝까지
p1_end = sec.find("</hp:p>", first_end) + len("</hp:p>")
p2_end = sec.find("</hp:p>", p1_end) + len("</hp:p>")
sec = sec[:p1_end] + sec[p2_end:]

THIN = f'<hp:p id="2147483648" paraPrIDRef="{new_pid}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="{new_id}"/></hp:p>'
extra_ids = []
hdr = header2
for j, h in enumerate((20, 40, 60, 80)):
    cid = new_id + 1 + j
    cpj = re.sub(r'id="0"', f'id="{cid}"', m.group(0), count=1)
    cpj = re.sub(r'height="\d+"', f'height="{h}"', cpj, count=1)
    hdr = hdr.replace("</hh:charProperties>", cpj + "</hh:charProperties>")
    extra_ids.append((h, cid))
c2 = re.search(r'<hh:charProperties itemCnt="(\d+)"', hdr)
hdr = hdr.replace(c2.group(0), f'<hh:charProperties itemCnt="{int(c2.group(1)) + 4}"')
for h, cid in extra_ids:
    one = f'<hp:p id="2147483648" paraPrIDRef="{new_pid}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="{cid}"/></hp:p>'
    s2 = sec[:first_end] + THIN * 14 + one + sec[first_end:]
    with zipfile.ZipFile(os.path.join(base, "in", f"h{h:03d}.hwpx"), "w") as w:
        for info, data in entries:
            if info.filename == "Contents/section0.xml":
                data = s2.encode("utf-8")
            elif info.filename == "Contents/header.xml":
                data = hdr.encode("utf-8")
            w.writestr(info, data, compress_type=zipfile.ZIP_STORED if info.filename == "mimetype" else zipfile.ZIP_DEFLATED)
print(sorted(os.listdir(os.path.join(base, "in"))))
