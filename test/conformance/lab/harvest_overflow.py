"""칸 내용(마지막 줄 끝 + 위아래 여백)이 한/글 행 높이보다 큰 칸을 모아 넘친 양을 무엇으로 설명할 수 있는지 센다.

    python harvest_overflow.py [--samples 유형]

행 높이 = 같은 행 rowSpan=1 칸 cellSz 최댓값(한/글 재저장본은 이 값을 실제 행 높이로 다시 적는다).
여백: hasMargin=1 이면 칸 cellMargin, 아니면 표 inMargin. 설명 후보:
  빈 끝 문단(마지막 문단이 비어 있고 그 줄을 빼면 들어감), 아래 여백(여백을 빼면 들어감), 마지막 줄(줄 하나를 빼면 들어감)
"""

import collections
import glob
import os
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
from harvest_tblsplit import tables, tcs  # noqa: E402


def paras_of(cell_xml):
    """칸 subList 바로 아래 문단(안쪽 표 문단 제외)마다 (글, [(vpos, vsize, spacing)])"""
    sub = cell_xml[cell_xml.find("<hp:subList") : cell_xml.rfind("</hp:subList>")]
    sub = re.sub(r"<hp:tbl\b.*?</hp:tbl>", "<TBL/>", sub, flags=re.S)
    out = []
    for p in re.findall(r"<hp:p\b.*?</hp:p>", sub, flags=re.S):
        text = "".join(re.findall(r"<hp:t>([^<]*)", p))
        segs = [
            tuple(int(x) for x in m)
            for m in re.findall(
                r'<hp:lineseg [^>]*vertpos="(\d+)" vertsize="(\d+)"[^>]*spacing="(-?\d+)"',
                p,
            )
        ]
        out.append(
            (
                text,
                segs,
                "<TBL/>" in p
                or "<hp:pic" in p
                or "<hp:rect" in p
                or "<hp:equation" in p,
            )
        )
    return out


def main():
    want = (
        sys.argv[sys.argv.index("--samples") + 1] if "--samples" in sys.argv else None
    )
    stat = collections.Counter()
    samples = collections.defaultdict(list)
    for path in sorted(glob.glob("../out/oracle/d*.hwpx")):
        doc = os.path.basename(path)[:-5]
        z = zipfile.ZipFile(path)
        for n in sorted(
            x for x in z.namelist() if re.match(r"Contents/section\d+\.xml$", x)
        ):
            xml = z.read(n).decode()
            for t in tables(xml):
                head = re.match(r"<hp:tbl\b[^>]*>", t).group(0)
                inm = re.search(
                    r'<hp:inMargin [^>]*top="(\d+)" bottom="(\d+)"',
                    t[: t.find("<hp:tr")],
                )
                it, ib = (int(inm.group(1)), int(inm.group(2))) if inm else (0, 0)
                rows = collections.defaultdict(int)
                cells = []
                for tc in tcs(t[len(head) :]):
                    tail = tc[tc.rfind("</hp:subList>") :]
                    a = re.search(
                        r'rowAddr="(\d+)"/><hp:cellSpan colSpan="\d+" rowSpan="(\d+)"/><hp:cellSz width="\d+" height="(\d+)"/>(?:<hp:cellMargin [^>]*top="(\d+)" bottom="(\d+)")?',
                        tail,
                    )
                    if not a or a.group(2) != "1":
                        continue
                    r = int(a.group(1))
                    rows[r] = max(rows[r], int(a.group(3)))
                    if 'hasMargin="1"' in tc[:200] and a.group(4):
                        mt, mb = int(a.group(4)), int(a.group(5))
                    else:
                        mt, mb = it, ib
                    va = re.search(r'vertAlign="(\w+)"', tc[:600])
                    cells.append((r, paras_of(tc), mt, mb, va.group(1) if va else "?"))
                for r, ps, mt, mb, va in cells:
                    segs = [s for _, ss, _ in ps for s in ss]
                    if not segs or any(obj for *_, obj in ps):
                        continue
                    end = max(v + h for v, h, _ in segs)
                    h = rows[r]
                    over = end + mt + mb - h
                    if over <= 0:
                        continue
                    last_text, last_segs, _ = ps[-1]
                    if not last_text.strip() and len(ps) > 1 and last_segs:
                        prev_end = max(
                            (v + hh for _, ss, _ in ps[:-1] for v, hh, _ in ss),
                            default=0,
                        )
                        kind = (
                            "빈 끝 문단"
                            if prev_end + mt + mb <= h
                            else "빈 끝 문단(빼도 넘침)"
                        )
                    elif end + mt <= h:
                        kind = "아래 여백 안"
                    elif end <= h:
                        kind = "여백 위아래 안"
                    else:
                        kind = "내용 자체가 큼"
                    key = (kind, va)
                    stat[key] += 1
                    if len(samples[kind]) < 8:
                        samples[kind].append(
                            (
                                doc,
                                r,
                                h,
                                end,
                                mt,
                                mb,
                                over,
                                va,
                                [(tx[:12], ss) for tx, ss, _ in ps][-3:],
                            )
                        )
    for k, v in stat.most_common():
        print(v, k)
    if want:
        for s in samples[want]:
            print(s)


if __name__ == "__main__":
    main()
