"""정답본(한/글 줄 배치)에서 위 간격 있는 문단이 쪽 끝에 걸린 경우를 모아, 쪽 맞춤 판정이 위 간격을 세는지 본다.

    python exp/harvest_fit_sb.py

본문 문단(표 칸 밖, 표, 개체 없는 글 문단)만. 앞 문단 끝 = 앞 문단 마지막 줄 vpos + 높이 + 줄 간격.
- 넘김: 이 문단 첫 줄이 다음 쪽(vpos 되감김)이고, 위 간격 없이는 들어가지만(끝 + 첫 줄 높이 ≤ 본문) 위 간격을 더하면 넘친다
  → 위 간격을 센다는 증거
- 담음: 이 문단 첫 줄이 같은 쪽인데 끝 + 위 간격 + 첫 줄 높이 > 본문 → 위 간격을 세지 않는다는 증거
간격은 hp:case(실제 값).
"""

import collections
import glob
import re
import sys
import zipfile
from pathlib import Path

from lxml import etree

sys.stdout.reconfigure(encoding="utf-8")
HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
OUT = Path(__file__).resolve().parent.parent.parent / "out"


def spacing(h, pid, key):
    pp = re.search(rf'<hh:paraPr id="{pid}"[\s\S]*?</hh:paraPr>', h).group(0)
    m = re.search(rf'<hc:{key} value="(-?\d+)"', pp.split("<hp:default>")[0])
    return int(m.group(1)) if m else 0


moved, kept = [], []
for f in sorted(glob.glob(str(OUT / "oracle" / "*.hwpx"))):
    z = zipfile.ZipFile(f)
    h = z.read("Contents/header.xml").decode("utf-8", "replace")
    for name in sorted(
        n for n in z.namelist() if re.match(r"Contents/section\d+\.xml", n)
    ):
        raw = z.read(name)
        pg = re.search(rb'<hp:pagePr[^>]*height="(\d+)"', raw)
        mg = re.search(rb"<hp:margin ([^>]*)>", raw)
        if not pg or not mg:
            continue
        mv = {k.decode(): int(v) for k, v in re.findall(rb'(\w+)="(\d+)"', mg.group(1))}
        body = int(pg.group(1)) - mv["top"] - mv["bottom"] - mv["header"] - mv["footer"]
        if b'colCount="2"' in raw or b'colCount="3"' in raw:
            continue
        root = etree.fromstring(raw)
        ps = [p for p in root if p.tag == f"{HP}p"]
        for i in range(1, len(ps)):
            p, prev = ps[i], ps[i - 1]
            if (
                p.find(f".//{HP}tbl") is not None
                or prev.find(f".//{HP}tbl") is not None
            ):
                continue
            if (
                p.find(f".//{HP}pic") is not None
                or prev.find(f".//{HP}pic") is not None
                or p.find(f".//{HP}ctrl") is not None
            ):
                continue
            if p.get("pageBreak") == "1" or p.get("columnBreak") == "1":
                continue
            ls = p.findall(f"{HP}linesegarray/{HP}lineseg")
            pls = prev.findall(f"{HP}linesegarray/{HP}lineseg")
            if not ls or not pls:
                continue
            sb = spacing(h, p.get("paraPrIDRef"), "prev")
            if sb <= 0:
                continue
            last = pls[-1]
            end = (
                int(last.get("vertpos"))
                + int(last.get("vertsize"))
                + int(last.get("spacing"))
                + spacing(h, prev.get("paraPrIDRef"), "next")
            )
            lh = int(ls[0].get("vertsize"))
            lsp = int(ls[0].get("spacing"))
            first = int(ls[0].get("vertpos"))
            new_page = first < int(last.get("vertpos"))
            # 빈 문단은 쪽 바닥을 넘어도 그 쪽에 남는다(d321 p66, p124, d330 p30, p31) — 따로 뺀다
            if not "".join(t.text or "" for t in p.iter(f"{HP}t")).strip():
                continue
            rec = (Path(f).stem, name[-12:], i, end, sb, lh, lsp, len(ls), body, first)
            # 앞 쪽 바닥 근처만: 위 간격 + 첫 줄(+줄 간격)로 넘칠 수 있는 범위
            if new_page and end + lh <= body:
                moved.append(rec)
            if not new_page and end + sb + lh > body - 2000:
                kept.append(rec)


def show(title, rows):
    print(title, len(rows))
    c = collections.Counter()
    for r in rows:
        _, _, _, end, sb, lh, lsp, n, body, _ = r
        key = (
            "줄만" if end + lh > body else "",
            "간격" if end + sb + lh > body else "",
            "간격+줄간" if end + sb + lh + lsp > body else "",
            "줄+줄간" if end + lh + lsp > body else "",
        )
        c[key] += 1
    for k, v in c.most_common():
        print("  ", k, v)
    for r in rows[:12]:
        print("    ", r)


show("다음 쪽으로 넘어간 첫 줄(위 간격 없이 들어감)", moved)
show("같은 쪽에 남은 바닥 근처 첫 줄", kept)
