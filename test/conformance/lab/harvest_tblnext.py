"""글자처럼 취급이 아닌 표만 담은 본문 문단에서 한/글이 쓴 높이(다음 문단 vertpos - 이 문단 vertpos)를 표 높이, 바깥 여백, 문단 위아래 간격과 맞댄다.

    python harvest_tblnext.py
"""
import collections
import glob
import os
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
from pagediff import body_xml  # noqa: E402

stat = collections.Counter()
samples = collections.defaultdict(list)
for path in sorted(glob.glob("../out/oracle/d*.hwpx")):
    doc = os.path.basename(path)[:-5]
    try:
        ps = body_xml(path)
        h = zipfile.ZipFile(path).read("Contents/header.xml").decode()
    except Exception:
        continue
    for i in range(len(ps) - 1):
        p, q = ps[i], ps[i + 1]
        if p.count("<hp:tbl ") != 1:
            continue
        outer = re.sub(r"<hp:tbl\b.*</hp:tbl>", "", p, flags=re.S)
        if re.search(r"<hp:t>[^<]", outer) or "<hp:pic" in outer or "<hp:rect" in outer:
            continue
        tbl = re.search(r"<hp:tbl\b[^>]*>", p).group(0)
        pos = re.search(r"<hp:pos [^>]*/>", p).group(0)
        if 'treatAsChar="1"' in pos or 'textWrap="TOP_AND_BOTTOM"' not in tbl:
            continue
        if 'vertRelTo="PARA"' not in pos or 'vertOffset="0"' not in pos:
            continue
        v0 = re.findall(r'<hp:lineseg [^>]*vertpos="(\d+)"', outer)
        v1 = re.findall(r'<hp:lineseg [^>]*vertpos="(\d+)"', re.sub(r"<hp:tbl\b.*</hp:tbl>", "", q, flags=re.S))
        if not v0 or not v1 or int(v1[0]) <= int(v0[0]):
            continue
        used = int(v1[0]) - int(v0[0])
        th = int(re.search(r'<hp:sz [^>]*height="(\d+)"', p).group(1))
        om = re.search(r'<hp:outMargin [^>]*top="(\d+)" bottom="(\d+)"', p)
        omt, omb = (int(om.group(1)), int(om.group(2))) if om else (0, 0)
        pid = re.search(r'paraPrIDRef="(\d+)"', p).group(1)
        pp = re.search(rf'<hh:paraPr id="{pid}"[\s\S]*?</hh:paraPr>', h).group(0)
        mg = re.search(r"<hp:case[\s\S]*?</hp:case>", pp) or re.search(r"<hh:margin>[\s\S]*?</hh:margin>", pp)
        nxt = int(re.search(r'<hc:next value="(-?\d+)"', mg.group(0)).group(1))
        qid = re.search(r'paraPrIDRef="(\d+)"', q).group(1)
        qp = re.search(rf'<hh:paraPr id="{qid}"[\s\S]*?</hh:paraPr>', h).group(0)
        qm = re.search(r"<hp:case[\s\S]*?</hp:case>", qp) or re.search(r"<hh:margin>[\s\S]*?</hh:margin>", qp)
        qprev = int(re.search(r'<hc:prev value="(-?\d+)"', qm.group(0)).group(1))
        base = th + omt + omb
        d = used - base
        if nxt == 0:
            key = "next 0"
        else:
            key = "next>0: " + ("next 더함" if d == nxt else "next 안 더함" if d == 0 else "다른 값")
        if qprev:
            key += " (다음 prev>0)"
        stat[key] += 1
        if len(samples[key]) < 6:
            samples[key].append((doc, i, used, th, omt, omb, nxt, qprev, d))
for k, n in stat.most_common():
    print(n, k)
    for s in samples[k]:
        print("    ", s)
