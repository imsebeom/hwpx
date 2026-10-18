"""글 없는 본문 문단에 위아래 배치(TOP_AND_BOTTOM, 글자처럼 취급 아님, 문단 기준) 그림이나 개체 하나만 있을 때
한/글이 다음 문단까지 얼마나 내려가는지 센다.

    python harvest_floatpic.py [--list]

step = 다음 문단 vpos - 이 문단 vpos 를 개체 아래(세로 오프셋 + 높이 + 바깥 여백 위아래)와 줄(높이 + 간격), 문단 간격에 맞대어 본다.
같은 쪽(다음 vpos 가 더 큼)인 경우만.
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
rows = []
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
            objs = re.findall(
                r"<hp:(pic|tbl|rect|container|ellipse|line|ole|equation)\b", own
            )
            if len(objs) != 1:
                continue
            kind = objs[0]
            m = re.search(
                r"<hp:"
                + kind
                + r"\b.*?<hp:sz [^>]*height=\"(\d+)\".*?<hp:pos ([^>]*)>.*?<hp:outMargin [^>]*top=\"(\d+)\" bottom=\"(\d+)\"",
                own,
                re.S,
            )
            if not m:
                continue
            height, pos, mt, mb = (
                int(m.group(1)),
                m.group(2),
                int(m.group(3)),
                int(m.group(4)),
            )
            if 'treatAsChar="0"' not in pos or 'vertRelTo="PARA"' not in pos:
                continue
            wrap = re.search(r"<hp:" + kind + r'\b[^>]*textWrap="(\w+)"', own).group(1)
            if wrap != "TOP_AND_BOTTOM":
                continue
            voff = int(re.search(r'vertOffset="(-?\d+)"', pos).group(1))
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
            step = nv - v
            pa = margins.get(re.search(r'paraPrIDRef="(\d+)"', a).group(1), (0, 0))
            pb = margins.get(re.search(r'paraPrIDRef="(\d+)"', b).group(1), (0, 0))
            obj = voff + height + mt + mb
            line = lh + ls
            cands = {
                "개체": obj,
                "개체+줄": obj + line,
                "개체+간격": obj + pa[1] + pb[0],
                "개체+줄+간격": obj + line + pa[1] + pb[0],
                "max(개체,줄)+간격": max(obj, line) + pa[1] + pb[0],
                "개체-앞위": obj - pb[0],
                "개체-자기위": obj - pa[0],
                "개체-자기위+다음위": obj - pa[0] + pb[0],
            }
            fit = [k for k, c in cands.items() if abs(step - c) <= 2]
            key = (kind, "/".join(fit) if fit else "모두 아님")
            stat[key] += 1
            if len(ex[key]) < 4:
                ex[key].append(
                    f"{doc} v={v} step={step} off={voff} h={height} m={mt},{mb} line={lh}+{ls} sa={pa[1]} sb={pb[0]} 자기위={pa[0]}"
                )
for k, n in stat.most_common():
    print(n, k, ex[k])
