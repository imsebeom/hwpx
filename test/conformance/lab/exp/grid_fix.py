"""효과 미리 재기: 표 열 격자로 칸 폭을 다시 적은 사본을 만든다.

열 폭: 그 열에서 시작하는 단일 열 칸 폭의 최빈값. 없으면 병합 칸에서 빼서 구한다(걸친 열 가운데 하나만 모를 때).
마지막 열: 표 폭 - 나머지 열 합(양수일 때). 칸 폭 = 걸친 열 폭의 합. 열을 다 못 구하거나 칸 간격이 있는 표는 그대로.

    python grid_fix.py <rt 폴더> <출력 폴더> [--no-last]
"""

import collections
import os
import re
import sys
import zipfile

src, dst = sys.argv[1], sys.argv[2]
no_last = "--no-last" in sys.argv
os.makedirs(dst, exist_ok=True)
stat = collections.Counter()
CELL = re.compile(
    r'<hp:cellAddr colAddr="(\d+)" rowAddr="(\d+)"/><hp:cellSpan colSpan="(\d+)" rowSpan="(\d+)"/><hp:cellSz width="(\d+)"'
)


def fix(t):
    if t.count("<hp:tbl ") > 1 or int(re.search(r'cellSpacing="(\d+)"', t).group(1)):
        return t
    tw = int(re.search(r'<hp:sz width="(\d+)"', t).group(1))
    cols = int(re.search(r'colCnt="(\d+)"', t).group(1))
    cells = [tuple(map(int, m.groups())) for m in CELL.finditer(t)]
    nrows = int(re.search(r'rowCnt="(\d+)"', t).group(1))
    occ = collections.Counter()
    for col, row, cs, rs, w in cells:
        for r in range(row, row + rs):
            for c in range(col, col + cs):
                occ[(r, c)] += 1
    if any(v != 1 for v in occ.values()) or len(occ) != nrows * cols:
        stat["격자 깨짐"] += 1
        return t
    single = collections.defaultdict(list)
    for col, row, cs, rs, w in cells:
        if cs == 1:
            single[col].append(w)
    width = [
        collections.Counter(single[c]).most_common(1)[0][0] if single[c] else None
        for c in range(cols)
    ]
    for _ in range(cols):
        for col, row, cs, rs, w in cells:
            span = range(col, min(col + cs, cols))
            unk = [c for c in span if width[c] is None]
            if len(unk) == 1:
                width[unk[0]] = w - sum(width[c] for c in span if width[c] is not None)
    if any(v is None or v <= 0 for v in width):
        stat["못 풂"] += 1
        return t
    if not no_last and tw > sum(width[:-1]):
        width[-1] = tw - sum(width[:-1])
    changed = False
    out, last = [], 0
    for m in CELL.finditer(t):
        col, row, cs, rs, w = map(int, m.groups())
        nw = sum(width[col : col + cs])
        if nw != w:
            changed = True
            out.append(t[last : m.start(5)])
            out.append(str(nw))
            last = m.end(5)
    out.append(t[last:])
    stat["바꾼 표" if changed else "같은 표"] += 1
    return "".join(out)


for f in sorted(os.listdir(src)):
    if not f.endswith(".hwpx"):
        continue
    zi = zipfile.ZipFile(os.path.join(src, f))
    with zipfile.ZipFile(os.path.join(dst, f), "w", zipfile.ZIP_DEFLATED) as zo:
        for i in zi.infolist():
            d = zi.read(i.filename)
            if re.match(r"Contents/section\d+\.xml$", i.filename):
                d = re.sub(
                    r"<hp:tbl .*?</hp:tbl>",
                    lambda m: fix(m.group(0)),
                    d.decode("utf-8"),
                    flags=re.S,
                ).encode("utf-8")
            zo.writestr(i, d)
print(dict(stat))
