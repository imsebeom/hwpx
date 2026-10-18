"""칸 문단의 왼쪽 여백, 들여쓰기(내어쓰기)를 한/글이 지키는지 무시하는지 칸 안쪽 폭과 함께 센다.

    python harvest_narrowmargin.py [--list]

둘째 줄이 있는 칸 문단만 본다. 예상 horzpos(둘째 줄) = 왼쪽 + max(0, -들여쓰기), 첫 줄 = 왼쪽 + max(0, 들여쓰기).
한/글 줄 기록 horzpos 가 예상과 같으면 「지킴」, 0 이면 「무시」. 남는 폭 = 줄 폭(첫 줄 horzpos + horzsize, 곧 칸 안쪽 폭) - 예상 들여 쓴 양 - 오른쪽.
"""

import collections
import glob
import os
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
rows = []
for path in sorted(glob.glob("../out/oracle/*.hwpx")):
    doc = os.path.basename(path)[:-5]
    z = zipfile.ZipFile(path)
    h = z.read("Contents/header.xml").decode("utf-8", "replace")
    pps = {}
    for m in re.finditer(r'<hh:paraPr id="(\d+)".*?</hh:paraPr>', h, re.S):
        case = re.search(r"<hp:case\b.*?</hp:case>", m.group(0), re.S)
        src = case.group(0) if case else m.group(0)
        vals = []
        for k in ("left", "right", "intent"):
            mm = re.search(r"<hc:%s value=\"(-?\d+)\"" % k, src)
            vals.append(int(mm.group(1)) if mm else 0)
        pps[m.group(1)] = tuple(vals)
    for name in [n for n in z.namelist() if re.match(r"Contents/section\d+\.xml$", n)]:
        s = z.read(name).decode("utf-8")
        for sub in re.finditer(r"<hp:subList\b[^>]*>(.*?)</hp:subList>", s, re.S):
            body = sub.group(1)
            if "<hp:subList" in body:
                continue
            for p in re.findall(r"<hp:p [^>]*>.*?</hp:p>", body, re.S):
                pp = re.search(r'paraPrIDRef="(\d+)"', p).group(1)
                left, right, ind = pps.get(pp, (0, 0, 0))
                if left == 0 and ind == 0:
                    continue
                segs = re.findall(r'horzpos="(-?\d+)" horzsize="(\d+)"', p)
                if len(segs) < 2:
                    continue
                h0, w0 = (int(x) for x in segs[0])
                h1, w1 = (int(x) for x in segs[1])
                full = h0 + w0 + right  # 칸 안쪽 폭(첫 줄 기준)
                exp1 = left + max(0, -ind)
                exp0 = left + max(0, ind)
                if h1 == exp1 and h0 == exp0:
                    k = "지킴"
                elif h1 == 0 and h0 == 0:
                    k = "무시"
                else:
                    k = "기타"
                rest = full - exp1 - right
                rows.append((k, doc, full, left, right, ind, rest, h0, h1))
stat = collections.Counter(r[0] for r in rows)
print(stat)
for k in ("무시", "기타"):
    xs = [r for r in rows if r[0] == k]
    print("==", k, len(xs))
    for r in sorted(xs, key=lambda r: r[6])[:12]:
        print("  ", r)
keep = sorted((r for r in rows if r[0] == "지킴"), key=lambda r: r[6])
print("== 지킴, 남는 폭이 작은 것")
for r in keep[:12]:
    print("  ", r)


def kind(r):
    # 여백 종류: 왼쪽만(들여쓰기 0), 내어쓰기(들여쓰기 < 0), 들여쓰기(> 0)
    return "왼쪽" if r[5] == 0 else ("내어쓰기" if r[5] < 0 else "들여쓰기")


print("== 종류별: 무시 남는 폭 최대, 지킴 남는 폭 최소, 비율(남는 폭 / 칸 안쪽 폭)")
for kd in ("왼쪽", "내어쓰기", "들여쓰기"):
    ign = [r for r in rows if r[0] == "무시" and kind(r) == kd]
    kp = [r for r in rows if r[0] == "지킴" and kind(r) == kd]
    mx = max((r[6] for r in ign), default=None)
    mn = min((r[6] for r in kp), default=None)
    rmx = max((r[6] / r[2] for r in ign), default=None)
    rmn = min((r[6] / r[2] for r in kp), default=None)
    print(kd, "무시", len(ign), "최대", mx, "비율최대", rmx and round(rmx, 3), "| 지킴", len(kp), "최소", mn, "비율최소", rmn and round(rmn, 3))
