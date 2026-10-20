"""한 문서의 본문 문단마다 한/글 쪽(vpos 되감김으로 센 것)과 엔진 쪽의 차가 바뀌는 곳을 찍는다.

    python exp/ppdiff.py d268 [정답본 폴더, 기본 ../out/oracle — 새 정답본은 ../out/fresh/rt]

한/글 쪽은 표가 쪽을 넘기면 되감김이 없어 덜 센다. 그래서 차가 한 번 바뀐 뒤 그대로면 그곳이 갈림이거나 못 센 쪽이다.
"""

import atexit
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nativescore import one  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
OUT = Path(__file__).resolve().parent.parent.parent / "out"
name = sys.argv[1]
src = Path(sys.argv[2]) if len(sys.argv) > 2 else OUT / "oracle"
tmp = tempfile.mkdtemp()
atexit.register(shutil.rmtree, tmp, True)
_, _, _, _, _, (pages, pp, han) = one(str(src / f"{name}.hwpx"), tmp)
print("엔진 쪽", pages, "한/글 vpos 쪽", han[-1] + 1 if han else None)
prev = None
for i, (a, b) in enumerate(zip(pp, han)):
    d = a - b
    if d != prev:
        print(f"p{i}: 한/글 {b + 1}쪽, 엔진 {a + 1}쪽 (차 {d:+d})")
        prev = d
