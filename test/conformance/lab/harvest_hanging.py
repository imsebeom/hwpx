"""칸 안 내어쓰기(들여쓰기 < 0) 문단을 남는 폭 비율(줄 폭 - 내어쓰기 - 왼쪽 - 오른쪽) / 줄 폭 으로 정렬하고,
엔진 줄바꿈이 한/글과 맞는지(불일치 목록에 있는지) 나란히 센다.

    python harvest_hanging.py <불일치.jsonl>

칸 번호는 nativescore 와 같다(<hp:tc> 아래 subList 차례). 한/글 줄이 둘 이상인 문단만.
"""

import collections
import glob
import json
import os
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
bad = set()
for line in open(sys.argv[1], encoding="utf-8"):
    r = json.loads(line)
    if r.get("where") == "칸":
        bad.add((r["id"], r["cell"], r["para"]))
TOK = re.compile(r"<(/?)hp:(p|subList|tc)\b([^>]*?)(/?)>")
buckets = collections.defaultdict(lambda: [0, 0])
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
    names = sorted(
        (n for n in z.namelist() if re.match(r"Contents/section\d+\.xml$", n)),
        key=lambda n: int(re.findall(r"\d+", n)[-1]),
    )
    cell_idx = -1
    for n in names:
        s = z.read(n).decode("utf-8")
        stack = []
        for m in TOK.finditer(s):
            close, name, selfc = m.group(1) == "/", m.group(2), m.group(4) == "/"
            if close:
                while stack:
                    if stack.pop()[0] == name:
                        break
                continue
            if name == "tc":
                if not selfc:
                    stack.append(("tc", None))
                continue
            if name == "subList":
                parent = stack[-1][0] if stack else None
                idx = -1
                if parent == "tc":
                    cell_idx += 1
                    idx = cell_idx
                if not selfc:
                    stack.append(("subList", [idx, 0]))
                continue
            if name == "p":
                sl = next((e for e in reversed(stack) if e[0] == "subList"), None)
                if sl is not None and sl[1][0] >= 0 and not selfc:
                    pi = sl[1][1]
                    sl[1][1] += 1
                    end = s.find("</hp:p>", m.end())
                    p = s[m.start() : end]
                    if "<hp:subList" not in p:
                        pp = re.search(r'paraPrIDRef="(\d+)"', p).group(1)
                        left, right, ind = pps.get(pp, (0, 0, 0))
                        segs = re.findall(r'horzpos="(-?\d+)" horzsize="(\d+)"', p)
                        if ind < 0 and len(segs) >= 2:
                            full = int(segs[0][0]) + int(segs[0][1])
                            rest = full - left - right + ind
                            ratio = rest / full if full else 0
                            ok = (doc, sl[1][0], pi) not in bad
                            b = min(int(ratio * 10), 9) if ratio > 0 else -1
                            buckets[b][0 if ok else 1] += 1
                            if ratio < 0.5:
                                rows.append(
                                    (
                                        "맞음" if ok else "다름",
                                        doc,
                                        sl[1][0],
                                        pi,
                                        full,
                                        left,
                                        right,
                                        ind,
                                        rest,
                                        round(ratio, 3),
                                    )
                                )
                if not selfc:
                    stack.append(("p", None))
                continue
print("남는 폭 비율 구간(0.1 단위, -1 은 음수): [맞음, 다름]")
for b in sorted(buckets):
    print(" ", b, buckets[b])
print("비율 0.5 미만")
for r in rows[:20]:
    print("  ", r)
