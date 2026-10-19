"""개발용: 열 때 합성한 칸 문단의 한 줄짜리 줄 배치도 그리기의 칸 재분할에서 다시 나누지 않는다.

    python apply_synth_single_row_keep.py [--revert]

recompose_cell_lines_in_frame 은 합성 줄이 두 줄 이상이면 「열 때 문서 속성으로 합성한 경계」라 그대로 두는데, 한 줄이면 「원본 기록이
아니다」 며 칸 안쪽 폭으로 다시 나눈다. d034 6쪽 표(칸 문단 여백 −800, −800, 들여쓰기 1000)는 열 때 합성한 줄이 한/글과 같은 한 줄(폭 11363,
한/글 11364)인데, 다시 나누면서 두 줄이 되어 행이 33.1px(한/글 27.6px)로 커지고 뒤 글이 21.9px 아래였다. 조판(줄바꿈 채점)은 이미 한 줄이다.
엔진이 만든(줄 폭이 있는) 한 줄도 경계를 그대로 둔다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx synth-single-row-keep]"

EDITS = [
    (
        "renderer/composer.rs",
        "    if para.line_segs.len() >= 2\n"
        "        && has_synthetic_line_segs\n"
        "        && !para.stored_text_partition_is_dirty()\n"
        "    {\n",
        f"    // {TAG} 엔진이 열 때 합성한(줄 폭이 있는) 한 줄도 경계를 그대로 둔다(d034 6쪽: 다시 나누면 한/글과 달리 두 줄)\n"
        "    if (para.line_segs.len() >= 2\n"
        "        || para.line_segs.first().is_some_and(|s| s.segment_width > 0))\n"
        "        && has_synthetic_line_segs\n"
        "        && !para.stored_text_partition_is_dirty()\n"
        "    {\n",
    ),
]


def main():
    revert = "--revert" in sys.argv
    edits = list(reversed(EDITS)) if revert else EDITS
    for rel, find, repl in edits:
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
            sys.exit(f"{rel}: 자리 {n}곳 — {find[:60]!r}")
        s = s.replace(find, repl)
        f.write_bytes(s.replace("\n", nl).encode("utf-8"))
        print("넣음", rel)


if __name__ == "__main__":
    main()
