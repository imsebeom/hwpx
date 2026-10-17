"""쪽을 넘는 표가 한/글에서 행 경계로 나뉘었는지(첫 조각 높이 = 행 높이 누적합) pageBreak 별로 센다.

    python harvest_tblsplit.py [--list]

한/글은 쪽을 넘는 표의 hp:sz height 에 첫 쪽 조각 높이만 적는다(REA hwpx_lab 실측). 행 높이는 rowSpan=1 칸 cellSz 의 최댓값.
"""
import collections
import glob
import os
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")


def tables(xml):
    for m in re.finditer(r"<hp:tbl\b", xml):
        depth, i = 0, m.start()
        for t in re.finditer(r"<hp:tbl\b|</hp:tbl>", xml[i:]):
            depth += 1 if t.group(0) == "<hp:tbl" else -1
            if depth == 0:
                yield xml[i : i + t.end()]
                break


def tcs(inner):
    """이 표의 칸(안쪽 표 칸 제외)"""
    out, depth, start = [], 0, None
    for m in re.finditer(r"<hp:tc\b|</hp:tc>|<hp:tbl\b|</hp:tbl>", inner):
        g = m.group(0)
        if g == "<hp:tbl":
            depth += 1
        elif g == "</hp:tbl>":
            depth -= 1
        elif depth == 0 and g == "<hp:tc":
            start = m.start()
        elif depth == 0 and g == "</hp:tc>" and start is not None:
            out.append(inner[start : m.end()])
            start = None
    return out


stat = collections.Counter()
rows_out = []
for path in sorted(glob.glob("../out/oracle/d*.hwpx")):
    doc = os.path.basename(path)[:-5]
    z = zipfile.ZipFile(path)
    for n in sorted(x for x in z.namelist() if re.match(r"Contents/section\d+\.xml$", x)):
        xml = z.read(n).decode()
        for t in tables(xml):
            head = re.match(r"<hp:tbl\b[^>]*>", t).group(0)
            pb = re.search(r'pageBreak="(\w+)"', head).group(1)
            if 'treatAsChar="1"' in t[: t.find("<hp:tr")]:
                continue
            # 안쪽 표를 지운 이 표의 행만
            inner = t[len(head) :]
            body = re.sub(r"<hp:subList\b.*?</hp:subList>", "", inner, flags=re.S)
            heights = collections.defaultdict(int)
            inm = re.search(r'<hp:inMargin [^>]*top="(\d+)" bottom="(\d+)"', t[: t.find("<hp:tr")])
            for tc in tcs(inner):
                a = re.search(r'<hp:cellAddr colAddr="\d+" rowAddr="(\d+)"/><hp:cellSpan colSpan="\d+" rowSpan="(\d+)"/><hp:cellSz width="\d+" height="(\d+)"/>(?:<hp:cellMargin [^>]*top="(\d+)" bottom="(\d+)")?', tc[tc.rfind("</hp:subList>"):])
                if not a or a.group(2) != "1":
                    continue
                own = re.sub(r"<hp:tbl\b.*</hp:tbl>", "", tc, flags=re.S)
                ends = [int(v) + int(h) for v, h in re.findall(r'<hp:lineseg [^>]*vertpos="(\d+)" vertsize="(\d+)"', own)]
                has = 'hasMargin="1"' in tc[:200]
                mt, mb = (int(a.group(4)), int(a.group(5))) if has and a.group(4) else ((int(inm.group(1)), int(inm.group(2))) if inm else (0, 0))
                content = (max(ends) + mt + mb) if ends else 0
                r = int(a.group(1))
                heights[r] = max(heights[r], int(a.group(3)), content)
            if len(heights) < 2:
                continue
            sz = int(re.search(r'<hp:sz [^>]*height="(\d+)"', t[: t.find("<hp:tr")]).group(1))
            hs = [heights[r] for r in sorted(heights)]
            total = sum(hs)
            if sz >= total - 50:
                continue  # 한 쪽에 다 들어감
            pref = [sum(hs[: k + 1]) for k in range(len(hs))]
            near = min(pref, key=lambda p: abs(p - sz))
            kind = "행 경계" if abs(near - sz) <= 60 else "행 안"
            stat[(pb, kind)] += 1
            rows_out.append((doc, pb, kind, sz, near, len(hs)))
for k, v in sorted(stat.items()):
    print(v, k)
if "--list" in sys.argv:
    for r in rows_out:
        print(r)
