"""글 없는 본문 문단에 용지, 쪽 기준(vertRelTo=PAPER/PAGE) 글자처럼 취급 아닌 개체만 있을 때 한/글이 그 빈 줄을 세는지 센다.

    python harvest_paperfloat.py

step = 다음 문단 vpos - 이 문단 vpos 를 줄(높이 + 간격) + 문단 간격과 0 에 맞대 본다. 같은 쪽(다음 vpos 가 더 큼)만.
"""

import collections
import glob
import os
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
stat = collections.Counter()
ex = collections.defaultdict(list)
for path in sorted(glob.glob("../out/oracle/*.hwpx")):
    doc = os.path.basename(path)[:-5]
    z = zipfile.ZipFile(path)
    h = z.read("Contents/header.xml").decode("utf-8", "replace")
    margins = {}
    for m in re.finditer(r'<hh:paraPr id="(\d+)".*?</hh:paraPr>', h, re.S):
        prev = re.search(r'<hc:prev value="(-?\d+)"', m.group(0))
        nxt = re.search(r'<hc:next value="(-?\d+)"', m.group(0))
        margins[m.group(1)] = (
            int(prev.group(1)) if prev else 0,
            int(nxt.group(1)) if nxt else 0,
        )
    for name in sorted(
        n for n in z.namelist() if re.match(r"Contents/section\d+\.xml$", n)
    ):
        s = z.read(name).decode("utf-8")
        paras = []
        depth, start = 0, -1
        for m in re.finditer(r"<(/?)hp:(p|subList)\b[^>]*?(/?)>", s):
            close, selfc = m.group(1) == "/", m.group(3) == "/"
            if m.group(2) == "subList":
                if not selfc:
                    depth += -1 if close else 1
                continue
            if depth:
                continue
            if not close and not selfc:
                start = m.start()
            elif close and start >= 0:
                paras.append(s[start : m.end()])
                start = -1
        for a, b in zip(paras, paras[1:]):
            own = re.sub(r"<hp:subList\b.*?</hp:subList>", "", a, flags=re.S)
            if re.search(r"<hp:t>[^<]", own):
                continue
            objs = list(
                re.finditer(
                    r"<hp:(pic|rect|container|ellipse|line|tbl|ole|textart)\b[^>]*textWrap=\"(\w+)\"",
                    own,
                )
            )
            if not objs:
                continue
            poss = re.findall(r"<hp:pos ([^>]*)>", own)
            if not poss or any('treatAsChar="1"' in p for p in poss):
                continue
            rel = {re.search(r'vertRelTo="(\w+)"', p).group(1) for p in poss}
            if not rel <= {"PAPER", "PAGE"}:
                continue
            segs = re.findall(
                r'<hp:lineseg textpos="\d+" vertpos="(-?\d+)" vertsize="(\d+)" textheight="\d+" baseline="\d+" spacing="(-?\d+)"',
                own,
            )
            nseg = re.search(
                r'<hp:lineseg textpos="\d+" vertpos="(-?\d+)"',
                re.sub(r"<hp:subList\b.*?</hp:subList>", "", b, flags=re.S),
            )
            if len(segs) != 1 or not nseg:
                continue
            v, lh, ls = (int(x) for x in segs[0])
            nv = int(nseg.group(1))
            if nv <= v:
                continue
            pa = margins.get(re.search(r'paraPrIDRef="(\d+)"', a).group(1), (0, 0))
            pb = margins.get(re.search(r'paraPrIDRef="(\d+)"', b).group(1), (0, 0))
            step = nv - v
            full = lh + ls + pa[1] + pb[0]
            wraps = "/".join(sorted({o.group(2) for o in objs}))
            k = (
                "줄 셈"
                if abs(step - full) <= 2
                else ("0" if step <= pb[0] + 2 else "기타"),
                wraps,
            )
            stat[k] += 1
            if len(ex[k]) < 3:
                ex[k].append(
                    f"{doc} v={v} step={step} line={lh}+{ls} sa={pa[1]} sb={pb[0]}"
                )
for k, n in stat.most_common():
    print(n, k, ex[k])
