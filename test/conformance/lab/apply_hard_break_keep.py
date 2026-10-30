"""개발용: 한/글이 저장한 칸 안 쪽 나눔 흔적이 있으면 첫 조각 최소 높이(25px)를 묻지 않는다.

    python apply_hard_break_keep.py [--revert]

근거(d129, d223): 병합 칸 블록의 칸 줄 위치가 0 으로 돌아가 한/글의 나눔 자리가 저장돼 있는데 첫 조각이 23.5px 라 거절, 블록 전체가 넘어가 1쪽 늘었다.
한/글 PDF 는 그 자리에서 한 줄을 남기고 나눈다.
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx hard-break-keep]"

EDITS = [
    (
        "renderer/typeset.rs",
        (
            "                    r == cursor_row\n"
            "                        || (res.hit_hard_break && res.consumed_height >= MIN_TOP_KEEP_PX)\n"
        ),
        (
            "                    r == cursor_row\n"
            f"                        // {TAG} HWPX 는 저장된 나눔 자리를 믿는다(d129: 첫 조각 23.5px 로 거절되면 1쪽 는다)\n"
            "                        || (res.hit_hard_break\n"
            "                            && (res.consumed_height >= MIN_TOP_KEEP_PX\n"
            "                                || (st.profile.hwpx_container() && res.consumed_height > 0.0)))\n"
        ),
    ),
]


def main():
    revert = "--revert" in sys.argv
    for rel, find, repl in EDITS:
        p = SRC / rel
        raw = p.read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in raw else "\n"
        s = raw.replace("\r\n", "\n")
        a, b = (repl, find) if revert else (find, repl)
        assert s.count(a) == 1, (rel, a[:70], s.count(a))
        p.write_bytes(s.replace(a, b).replace("\n", nl).encode("utf-8"))
    print("되돌림" if revert else "적용")


if __name__ == "__main__":
    main()
