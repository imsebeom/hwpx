"""본문 문단 하나에 든 표의 행 높이를 한/글(정답본 칸 줄 배치와 cellSz 중 큰 값)과 rhwp(DIAG_ROWH req)로 맞댄다. HWPUNIT.

    python rowcmp.py <id> <본문 문단>
"""
import collections
import os
import re
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")
from harvest_tblsplit import tcs  # noqa: E402
from nativescore import EXE, HERE, one  # noqa: E402
from pagediff import body_xml  # noqa: E402

doc, pi = sys.argv[1], int(sys.argv[2])
path = str(HERE.parent / "out" / "oracle" / f"{doc}.hwpx")
p = body_xml(path)[pi]
t = p[p.index("<hp:tbl ") :]
head = re.match(r"<hp:tbl\b[^>]*>", t).group(0)
inm = re.search(r'<hp:inMargin [^>]*top="(\d+)" bottom="(\d+)"', t[: t.find("<hp:tr")])
han = collections.defaultdict(int)
for tc in tcs(t[len(head) :]):
    tail = tc[tc.rfind("</hp:subList>") :]
    a = re.search(r'rowAddr="(\d+)"/><hp:cellSpan colSpan="\d+" rowSpan="(\d+)"/><hp:cellSz width="\d+" height="(\d+)"/>(?:<hp:cellMargin [^>]*top="(\d+)" bottom="(\d+)")?', tail)
    if not a or a.group(2) != "1":
        continue
    own = re.sub(r"<hp:tbl\b.*</hp:tbl>", "", tc, flags=re.S)
    ends = [int(v) + int(h) for v, h in re.findall(r'<hp:lineseg [^>]*vertpos="(\d+)" vertsize="(\d+)"', own)]
    has = 'hasMargin="1"' in tc[:200]
    mt, mb = (int(a.group(4)), int(a.group(5))) if has and a.group(4) else ((int(inm.group(1)), int(inm.group(2))) if inm else (0, 0))
    r = int(a.group(1))
    han[r] = max(han[r], int(a.group(3)), (max(ends) + mt + mb) if ends else 0)
tmp = tempfile.mkdtemp(prefix="rowcmp_")
one(path, tmp)
err = subprocess.run([str(EXE), os.path.join(tmp, f"{doc}.hwpx")], capture_output=True, text=True, encoding="utf-8",
                     env={**os.environ, "RHWP_DIAG_ROWH": "1", "CLAUDE_METRICS_DIR": str(HERE.parent / "out" / "metrics")}).stderr
rh = collections.defaultdict(float)
for m in re.finditer(rf"DIAG_ROWH pi={pi} ci=\d+ depth=0 r=(\d+) c=\d+ decl=([\d.]+) req=([\d.]+)", err):
    r = int(m.group(1))
    rh[r] = max(rh[r], float(m.group(2)) * 75, float(m.group(3)) * 75)
tot_h = tot_r = 0
for r in sorted(han):
    tot_h += han[r]
    tot_r += rh.get(r, 0)
    print(f"r{r:3d} 한글 {han[r]:6d} rhwp {rh.get(r, 0):8.0f} 차 {rh.get(r, 0) - han[r]:+7.0f}  누적차 {tot_r - tot_h:+7.0f}")
