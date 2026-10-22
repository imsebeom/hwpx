"""재저장본(한/글) 문단마다 둘째 줄 시작 자리를 글로 보인다(조판 부호 없는 한 run 문단만).

    python exp/breakat.py <재저장본.hwpx> [앞 글자 수=12]
한 줄: 문단 번호 | 줄 끝 앞 글자 ‖ 다음 줄 첫 글자
"""

import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
n = int(sys.argv[2]) if len(sys.argv) > 2 else 12
sec = zipfile.ZipFile(sys.argv[1]).read("Contents/section0.xml").decode("utf-8")
for i, p in enumerate(re.findall(r"<hp:p [\s\S]*?</hp:p>", sec)):
    text = "".join(re.findall(r"<hp:t>([^<]*)</hp:t>", p))
    starts = [int(x) for x in re.findall(r'<hp:lineseg textpos="(\d+)"', p)]
    if len(starts) < 2 or not text:
        continue
    b = starts[1]
    print(f"{i:3d} | {text[max(0, b - n) : b]!s} ‖ {text[b : b + 6]}")
