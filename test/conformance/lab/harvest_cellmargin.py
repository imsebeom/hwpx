"""hasMargin=0 칸이 위아래 여백으로 표 안쪽 여백(inMargin)과 칸 cellMargin 중 무엇을 쓰는지 정답본으로 가린다.

    python harvest_cellmargin.py

rowSpan=1 칸 중 한/글 행 높이(같은 행 칸 cellSz 최댓값)가 「내용 끝 + 여백」과 정확히 같은 칸만 센다(내용이 행을 결정한 칸).
"""
import collections
import glob
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
from harvest_tblsplit import tables, tcs  # noqa: E402

stat = collections.Counter()
for path in sorted(glob.glob("../out/oracle/d*.hwpx")):
    z = zipfile.ZipFile(path)
    for n in sorted(x for x in z.namelist() if re.match(r"Contents/section\d+\.xml$", x)):
        xml = z.read(n).decode()
        for t in tables(xml):
            head = re.match(r"<hp:tbl\b[^>]*>", t).group(0)
            inm = re.search(r'<hp:inMargin [^>]*top="(\d+)" bottom="(\d+)"', t[: t.find("<hp:tr")])
            if not inm:
                continue
            it, ib = int(inm.group(1)), int(inm.group(2))
            cells = []
            rowh = collections.defaultdict(int)
            for tc in tcs(t[len(head) :]):
                tail = tc[tc.rfind("</hp:subList>") :]
                a = re.search(r'rowAddr="(\d+)"/><hp:cellSpan colSpan="\d+" rowSpan="(\d+)"/><hp:cellSz width="\d+" height="(\d+)"/>(?:<hp:cellMargin [^>]*top="(\d+)" bottom="(\d+)")?', tail)
                if not a or a.group(2) != "1":
                    continue
                r = int(a.group(1))
                rowh[r] = max(rowh[r], int(a.group(3)))
                if 'hasMargin="1"' in tc[:200] or not a.group(4):
                    continue
                own = re.sub(r"<hp:tbl\b.*</hp:tbl>", "", tc, flags=re.S)
                if "<hp:pic" in own or "<hp:rect" in own or "<hp:equation" in own:
                    continue
                ends = [int(v) + int(h) for v, h in re.findall(r'<hp:lineseg [^>]*vertpos="(\d+)" vertsize="(\d+)"', own)]
                if not ends:
                    continue
                cells.append((r, max(ends), int(a.group(4)) + int(a.group(5))))
            if (it + ib) == 0:
                continue
            for r, end, cm in cells:
                if cm == it + ib:
                    continue
                h = rowh[r]
                if h == end + it + ib:
                    stat["표 안쪽 여백"] += 1
                elif h == end + cm:
                    stat["칸 cellMargin"] += 1
                elif h > max(end + it + ib, end + cm):
                    stat["행이 더 큼(판정 불가)"] += 1
                else:
                    stat[f"행이 작음: 안쪽 기준 {h - end - it - ib:+d}, 칸 기준 {h - end - cm:+d}"] += 1
for k, v in stat.most_common(12):
    print(v, k)
