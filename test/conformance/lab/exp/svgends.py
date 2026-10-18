"""네이티브 엔진(claude-linestarts, CLAUDE_SVG)으로 문서를 그려 쪽마다 처음과 끝 글(빈칸 뺀 16자)을 찍는다. 패치 전후 견주기용.

python exp/svgends.py <파일.hwpx> [쪽 수 상한]
"""

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
EXE = (
    Path.home()
    / ".claude/skills/hwpx/editor/.build/rhwp/target/debug/claude-linestarts.exe"
)
f = sys.argv[1]
lim = int(sys.argv[2]) if len(sys.argv) > 2 else 999
d = tempfile.mkdtemp()
subprocess.run([str(EXE), f], capture_output=True, env={**os.environ, "CLAUDE_SVG": d})
pages = sorted(Path(d).glob("*.svg"), key=lambda p: int(p.stem))
for p in pages[:lim]:
    s = p.read_text(encoding="utf-8")
    t = "".join(re.findall(r"<text\b[^>]*>([^<]*)</text>", s))
    t = re.sub(r"\s+", "", t)
    print(f"{int(p.stem) + 1:3d} {t[:16]} … {t[-16:]}")
