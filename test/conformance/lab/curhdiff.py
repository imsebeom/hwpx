"""본문 문단마다 한/글 첫 줄 vertpos 와 rhwp 조판 누적 높이(문단 시작 cur_h)를 HWPUNIT 로 맞댄다.

    python curhdiff.py <id> [시작 문단] [개수]

rhwp 값은 RHWP_DIAG_FLOW(글 문단)와 DIAG_TBLP(표 문단)의 cur_h(px × 75)다. 커서 y 와 달리 표 뒤 문단에서도 흔들리지 않는다.
쪽이 바뀌면(한/글 vertpos 되감김, rhwp page 증가) 차는 새 쪽 기준이다.
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
    tmp = tempfile.mkdtemp(prefix="curh_")
    path = str(HERE.parent / "out" / "oracle" / f"{doc}.hwpx")
    one(path, tmp)
    err = subprocess.run(
        [str(EXE), os.path.join(tmp, f"{doc}.hwpx")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "RHWP_DIAG_FLOW": "1", "CLAUDE_METRICS_DIR": str(HERE.parent / "out" / "metrics")},
    ).stderr
    cur = {}
    for m in re.finditer(r"DIAG_(?:FLOW|TBLP) pi=(\d+) cur_h=([\d.]+)(?: page=(\d+))?", err):
        cur.setdefault(int(m.group(1)), (float(m.group(2)), m.group(3)))
    paras = body_xml(path)
    print(f"{'p':>4} {'한글 vpos':>9} {'rhwp cur_h':>10} {'차':>7}  글")
    for i in range(start, min(len(paras), start + count)):
        segs = SEG.findall(paras[i])
        v = re.findall(r'vertpos="(-?\d+)"', segs[-1]) if segs else []
        hv = int(v[0]) if v else None
        rc = cur.get(i)
        rh = round(rc[0] * 75) if rc else None
        diff = rh - hv if (rh is not None and hv is not None) else ""
        txt = "".join(re.findall(r"<hp:t>([^<]*)</hp:t>", SEG.sub("", paras[i])))[:24]
        pg = rc[1] if rc and rc[1] else "-"
        print(f"{i:>4} {hv!s:>9} {rh!s:>10} {diff!s:>7}  쪽{pg} {txt!r}")


if __name__ == "__main__":
    main()
