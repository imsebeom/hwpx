"""첫 구역 본문 문단의 줄마다 한/글 줄 기록(vertsize/spacing)과 엔진(줄 배치 지운 사본)의 줄 높이/간격을 맞대어 어긋남을 센다.

    python segcmp.py <id> [보기 개수=10]

엔진 값은 claude-linestarts 의 CLAUDE_SEGV 출력(vpos/높이/간격)이다. 줄 수가 다른 문단은 따로 센다.
"""

import collections
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
EXE = (
    Path.home()
    / ".claude/skills/hwpx/editor/.build/rhwp/target/debug/claude-linestarts.exe"
)
SEG = re.compile(r"<hp:linesegarray>.*?</hp:linesegarray>", re.S)


def top_paras(xml):
    """본문(최상위) 문단마다 줄 기록 [(vertsize, spacing)]"""
    out, depth, start = [], 0, -1
    for m in re.finditer(r"<(/?)hp:(p|subList)\b[^>]*?(/?)>", xml):
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
            p = xml[start : m.start()]
            # 칸 안 줄 기록을 빼고 이 문단 자신의 것만
            own = re.sub(r"<hp:subList\b.*?</hp:subList>", "", p, flags=re.S)
            out.append(
                [
                    (int(a), int(b))
                    for a, b in re.findall(
                        r'vertsize="(\d+)" textheight="\d+" baseline="\d+" spacing="(-?\d+)"',
                        own,
                    )
                ]
            )
            start = -1
    return out


def main():
    doc = sys.argv[1]
    show = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    src = HERE.parent / "out" / "oracle" / f"{doc}.hwpx"
    z = zipfile.ZipFile(src)
    han = top_paras(z.read("Contents/section0.xml").decode("utf-8"))
    tmp = tempfile.mkdtemp()
    dst = os.path.join(tmp, f"{doc}.hwpx")
    with zipfile.ZipFile(dst, "w") as w:
        for info in z.infolist():
            data = z.read(info.filename)
            if re.match(r"Contents/section\d+\.xml$", info.filename):
                data = SEG.sub("", data.decode("utf-8")).encode("utf-8")
            w.writestr(
                info,
                data,
                compress_type=zipfile.ZIP_STORED
                if info.filename == "mimetype"
                else zipfile.ZIP_DEFLATED,
            )
    r = subprocess.run(
        [str(EXE), dst],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={
            **os.environ,
            "CLAUDE_SEGV": "1",
            "CLAUDE_METRICS_DIR": str(HERE.parent / "out" / "metrics"),
        },
    )
    eng = {}
    for line in r.stderr.splitlines():
        if line.startswith("SEGV "):
            parts = line.split()
            eng[int(parts[1])] = [
                tuple(int(x) for x in s.split("/")[1:]) for s in parts[2:]
            ]
    stat = collections.Counter()
    shown = 0
    for i, h in enumerate(han):
        e = eng.get(i, [])
        if not h:
            continue
        if len(h) != len(e):
            stat["줄 수 다름"] += 1
            continue
        for (hv, hs), (ev, es) in zip(h, e):
            key = "같음" if (abs(hv - ev) <= 2 and abs(hs - es) <= 4) else "다름"
            stat[key] += 1
            if key == "다름" and shown < show:
                print(f"  p{i} 한/글 {hv}/{hs} 엔진 {ev}/{es}")
                shown += 1
    print(doc, dict(stat))


if __name__ == "__main__":
    main()
