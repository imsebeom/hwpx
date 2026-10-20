"""문서를 네이티브 rhwp 로 그려 쪽마다 글 줄(같은 y 로 묶은 글자)을 찍는다. 단위 pt.

    python svglines.py <id 또는 hwpx 경로> [쪽 번호(0부터)] [y 하한] [y 상한]

정답본 id 면 줄 배치를 지운 사본을 그린다(채점과 같은 조건).
"""

import atexit
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")
from nativescore import EXE, HERE, one  # noqa: E402


def main():
    arg = sys.argv[1]
    tmp = tempfile.mkdtemp(prefix="svgl_")
    atexit.register(shutil.rmtree, tmp, True)
    out = tempfile.mkdtemp(prefix="svgo_")
    atexit.register(shutil.rmtree, out, True)
    if os.path.exists(arg):
        src = arg
        stem = os.path.splitext(os.path.basename(arg))[0]
    else:
        stem = arg
        one(str(HERE.parent / "out" / "oracle" / f"{arg}.hwpx"), tmp)
        src = os.path.join(tmp, f"{arg}.hwpx")
    subprocess.run(
        [str(EXE), src],
        capture_output=True,
        env={
            **os.environ,
            "CLAUDE_SVG": out,
            "CLAUDE_METRICS_DIR": str(HERE.parent / "out" / "metrics"),
        },
    )
    pages = sorted(int(f[:-4]) for f in os.listdir(out) if f.endswith(".svg"))
    want = int(sys.argv[2]) if len(sys.argv) > 2 else None
    lo = float(sys.argv[3]) if len(sys.argv) > 3 else 0
    hi = float(sys.argv[4]) if len(sys.argv) > 4 else 1e9
    print(stem, "쪽", len(pages))
    for pg in pages:
        if want is not None and pg != want:
            continue
        s = open(os.path.join(out, f"{pg}.svg"), encoding="utf-8").read()
        lines = {}
        for m in re.finditer(
            r'<text[^>]*?x="([\d.]+)"[^>]*?y="([\d.]+)"[^>]*>([^<]*)</text>', s
        ):
            y = round(float(m.group(2)) * 0.75, 1)
            lines.setdefault(y, []).append(
                (float(m.group(1)), html.unescape(m.group(3)))
            )
        print("== 쪽", pg)
        for y in sorted(lines):
            if lo <= y <= hi:
                xs = sorted(lines[y])
                print(
                    f"  {y:6.1f} {xs[0][0] * 0.75:6.1f} {''.join(t for _, t in xs)[:40]}"
                )


if __name__ == "__main__":
    main()
