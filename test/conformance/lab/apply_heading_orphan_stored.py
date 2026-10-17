"""개발용: 제목 외톨이 보정(Task #404)을 한/글이 저장한 줄 위치가 있을 때만 쓴다.

    python apply_heading_orphan_stored.py [--revert]

근거(d134): 보정은 「누적 높이로는 들어가지만 저장 vpos 로는 쪽 한계를 넘는」 문단을 다음 쪽으로 민다.
줄 기록이 없는 문서에서는 엔진이 만든 합성 줄(TAG_IMPLEMENTATION_PROPERTY)의 vpos 를 보게 되는데, 이 값은 쪽 나눔을
모르는 누적값이라 쪽 첫 문단 기준의 비교가 맞지 않는다. d134 p50(5줄, 쪽 아래 여유 충분)이 이 오판으로 다음 쪽에 밀렸다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx heading-orphan-stored]"

EDITS = [
    (
        "renderer/typeset.rs",
        "                if let (Some(first_seg), Some(page_top_vpos)) =\n"
        "                    (para.line_segs.first(), page_top_vpos_opt)\n"
        "                {\n",
        f"                // {TAG} 합성 줄(엔진이 만든 줄 기록)의 vpos 는 쪽 나눔을 모르는 누적값이라 이 보정에 쓰지 않는다.\n"
        "                let stored_first_seg = para\n"
        "                    .line_segs\n"
        "                    .first()\n"
        "                    .filter(|s| s.tag & LineSeg::TAG_IMPLEMENTATION_PROPERTY == 0);\n"
        "                if let (Some(first_seg), Some(page_top_vpos)) =\n"
        "                    (stored_first_seg, page_top_vpos_opt)\n"
        "                {\n",
    ),
]


def main():
    revert = "--revert" in sys.argv
    for rel, find, repl in EDITS:
        if revert:
            find, repl = repl, find
        f = SRC / rel
        raw = f.read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in raw else "\n"
        s = raw.replace("\r\n", "\n")
        if (find not in s) if revert else (repl in s):
            print("이미", rel)
            continue
        n = s.count(find)
        if n != 1:
            sys.exit(f"{rel}: 자리 {n}곳 — {find[:50]!r}")
        s = s.replace(find, repl)
        f.write_bytes(s.replace("\n", nl).encode("utf-8"))
        print("넣음", rel)


if __name__ == "__main__":
    main()
