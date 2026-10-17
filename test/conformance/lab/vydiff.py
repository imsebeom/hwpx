"""본문 문단마다 한/글 첫 줄 vertpos 와 rhwp 커서 y 를 HWPUNIT 로 맞대어, 문단 사이 간격이 어디서 벌어지는지 찍는다.

    python vydiff.py <id> [시작 문단] [개수]
같은 쪽 안에서 「다음 문단 시작 - 이 문단 시작」을 비교한다(rhwp 는 px × 75 = HWPUNIT, 쪽 머리 여백 차이는 지운다).
"""

import os
import re
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nativescore import EXE, HERE, one  # noqa: E402
from pagediff import SEG, body_xml  # noqa: E402


def main():
    doc = sys.argv[1]
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    tmp = tempfile.mkdtemp(prefix="vydiff_")
    path = str(HERE.parent / "out" / "oracle" / f"{doc}.hwpx")
    one(path, tmp)  # 줄 배치를 지운 사본을 tmp 에 만든다
    out = subprocess.run(
        [str(EXE), os.path.join(tmp, f"{doc}.hwpx")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "CLAUDE_VY": "1"},
    ).stdout
    vy = []
    for line in out.splitlines():
        parts = line.split("\t")
        if parts[1] == "VY":
            pg, y, _ = parts[3].split(":")
            vy.append((int(pg), round(float(y) * 75)))
    paras = body_xml(path)
    han = []
    for p in paras:
        segs = SEG.findall(p)
        attrs = re.findall(r"<hp:lineseg ([^>]*)/>", segs[-1]) if segs else []
        first = dict(re.findall(r'(\w+)="(-?\d+)"', attrs[0])) if attrs else {}
        han.append(
            (
                int(first.get("vertpos", -1)),
                len(attrs),
                int(first.get("vertsize", 0)),
                int(first.get("spacing", 0)),
            )
        )
    print(
        f"{'p':>4} {'한글 vpos':>9} {'Δ한글':>7} {'rhwp 쪽:y':>12} {'Δrhwp':>7} {'차':>6} 줄 크기 간격 조판부호 글"
    )
    for i in range(start, min(len(paras) - 1, start + count)):
        dh = han[i + 1][0] - han[i][0]
        dr = (
            vy[i + 1][1] - vy[i][1]
            if i + 1 < len(vy) and vy[i + 1][0] == vy[i][0]
            else None
        )
        ctrls = sorted(
            set(
                re.findall(
                    r"<hp:(tbl|pic|rect|equation|container|line|ellipse)\b",
                    SEG.sub("", paras[i]),
                )
            )
        )
        txt = "".join(re.findall(r"<hp:t>([^<]*)</hp:t>", SEG.sub("", paras[i])))[:24]
        diff = dr - dh if dr is not None and han[i + 1][0] > han[i][0] else None
        print(
            f"{i:>4} {han[i][0]:>9} {dh:>7} {vy[i][0]:>4}:{vy[i][1]:<7} {dr if dr is not None else '-':>7} {diff if diff is not None else '':>6} {han[i][1]} {han[i][2]} {han[i][3]} {ctrls} {txt!r}"
        )


if __name__ == "__main__":
    main()
