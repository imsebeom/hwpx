"""새 정답본에서 글(또는 빈칸, 탭)이 있는 문단에 자리 차지 표(문단 기준) 하나가 든 경우, 그 문단의 흐름 높이를 엔진과 한/글로 견준다.

    python exp/flow_texthost.py [rhwp.exe]

한/글 = 다음 문단 vpos − 앞 문단 끝(앞 문단 마지막 줄 vpos + 높이 + 줄 간격), 엔진 = RHWP_FLOW_DBG 의 cur_h 차(px → HU).
앞, 뒤 문단이 같은 쪽이고 앞 문단에 개체가 없는 것만. 간격(위, 아래)은 양쪽에 같이 들어간다.
"""

import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

from lxml import etree

sys.stdout.reconfigure(encoding="utf-8")
HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
OUT = Path(__file__).resolve().parent.parent.parent / "out"
EXE = (
    sys.argv[1]
    if len(sys.argv) > 1
    else str(
        Path.home() / ".claude/skills/hwpx/editor/.build/rhwp/target/debug/rhwp.exe"
    )
)
env = dict(os.environ, RHWP_FLOW_DBG="1", CLAUDE_METRICS_DIR=str(OUT / "metrics"))


def segs(p):
    return p.findall(f"{HP}linesegarray/{HP}lineseg")


def own_text(p):
    return "".join(
        t.text or ""
        for t in p.iter(f"{HP}t")
        if not any(a.tag == f"{HP}tbl" for a in t.iterancestors())
    )


cases = []
for f in sorted((OUT / "fresh" / "rt").glob("*.hwpx")):
    z = zipfile.ZipFile(f)
    names = sorted(n for n in z.namelist() if re.match(r"Contents/section\d+\.xml", n))
    for si, n in enumerate(names):
        root = etree.fromstring(z.read(n))
        ps = [p for p in root if p.tag == f"{HP}p"]
        for i in range(1, len(ps) - 1):
            p = ps[i]
            tb = [
                t
                for t in p.findall(f"{HP}run/{HP}tbl")
                if t.find(f"{HP}pos").get("treatAsChar") == "0"
                and t.get("textWrap") == "TOP_AND_BOTTOM"
                and t.find(f"{HP}pos").get("vertRelTo") == "PARA"
            ]
            tabs = [
                t
                for t in p.iter(f"{HP}tab")
                if not any(a.tag == f"{HP}tbl" for a in t.iterancestors())
            ]
            if len(tb) != 1 or not (own_text(p) or tabs):
                continue
            prev = ps[i - 1]
            if prev.findall(f"{HP}run/{HP}tbl") or prev.findall(f"{HP}run/{HP}pic"):
                continue
            pv, nx = segs(prev), segs(ps[i + 1])
            if not pv or not nx:
                continue
            prev_end = (
                int(pv[-1].get("vertpos"))
                + int(pv[-1].get("vertsize"))
                + int(pv[-1].get("spacing"))
            )
            nxt = int(nx[0].get("vertpos"))
            if nxt <= prev_end:
                continue
            kind = "글" if own_text(p).strip() else "빈칸/탭"
            cases.append((f.stem, si, i, kind, nxt - prev_end, len(segs(p))))

flow = {}
for stem in sorted({c[0] for c in cases}):
    out = subprocess.run(
        [EXE, "dump-pages", str(OUT / "fresh" / "in" / f"{stem}.hwpx"), "-p", "0"],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    sec = -1
    last = None
    for line in (out.stdout + out.stderr).splitlines():
        m = re.match(r"FLOW_DBG pi=(\d+) page=(\d+) cur_h=([-\d.]+)", line)
        if not m:
            continue
        pi = int(m.group(1))
        if last is None or pi <= last:
            sec += 1
        last = pi
        flow[(stem, sec, pi)] = (int(m.group(2)), float(m.group(3)))

same = 0
for stem, si, i, kind, han, nseg in cases:
    a, b, c = (
        flow.get((stem, si, i - 1)),
        flow.get((stem, si, i)),
        flow.get((stem, si, i + 1)),
    )
    if not (a and b and c) or c[0] != a[0]:
        print(stem, si, i, kind, "엔진 쪽이 다르거나 없음")
        continue
    # 앞 문단 끝 = 이 문단 시작(cur_h) 이라 본다
    eng = round((c[1] - b[1]) * 75)
    ok = abs(eng - han) <= 8
    same += ok
    print(
        stem,
        si,
        i,
        kind,
        "줄",
        nseg,
        "한/글",
        han,
        "엔진",
        eng,
        "같음" if ok else f"차 {eng - han}",
    )
print("같음", same, "/", len(cases))
