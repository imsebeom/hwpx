"""글 없이 글자처럼 취급 표만 든 본문 문단(줄 하나)에서 한/글이 다음 문단까지 얼마나 내려가는지 센다.

    python harvest_tacstep.py

다음 문단 vpos - 이 문단 vpos 를 「줄 높이 + 줄 간격」(전체)과 엔진 cap 「줄 높이 + 줄 간격/2 + 바깥 위 여백」에 맞대 본다.
같은 쪽(다음 vpos 가 더 큼)인 경우만. 문단 위아래 간격(paraPr prev/next)이 0 이 아니면 따로 센다.
"""

import collections
import glob
import os
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
from segcmp import top_paras  # noqa: E402,F401

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
            segs = re.findall(
                r'<hp:lineseg textpos="\d+" vertpos="(-?\d+)" vertsize="(\d+)" textheight="\d+" baseline="\d+" spacing="(-?\d+)"',
                own,
            )
            if len(segs) != 1 or re.search(r"<hp:t>[^<]", own):
                continue
            tbls = re.findall(
                r"<hp:tbl\b.*?<hp:pos ([^>]*)>.*?<hp:outMargin [^>]*top=\"(\d+)\"",
                own,
                re.S,
            )
            objs = re.findall(r"<hp:(tbl|pic|rect|container|equation)\b", own)
            if len(tbls) != 1 or len(objs) != 1 or 'treatAsChar="1"' not in tbls[0][0]:
                continue
            nb = re.sub(r"<hp:subList\b.*?</hp:subList>", "", b, flags=re.S)
            nseg = re.search(r'<hp:lineseg textpos="\d+" vertpos="(-?\d+)"', nb)
            if not nseg:
                continue
            v, lh, ls = (int(x) for x in segs[0])
            nv = int(nseg.group(1))
            if nv <= v:
                continue
            step = nv - v
            top = int(tbls[0][1])
            pa = margins.get(re.search(r'paraPrIDRef="(\d+)"', a).group(1), (0, 0))
            pb = margins.get(re.search(r'paraPrIDRef="(\d+)"', b).group(1), (0, 0))
            extra = pa[1] + pb[0]
            full = lh + ls + extra
            cap = lh + ls // 2 + top + extra
            if abs(step - full) <= 2:
                k = "전체"
            elif abs(step - cap) <= 2:
                k = "cap"
            else:
                k = "둘 다 아님"
            k = (k, "문단 간격 있음" if extra else "문단 간격 없음")
            stat[k] += 1
            if len(ex[k]) < 4:
                ex[k].append(
                    f"{doc} v={v} lh={lh} ls={ls} top={top} extra={extra} step={step}"
                )
for k, n in stat.most_common():
    print(n, k, ex[k])
