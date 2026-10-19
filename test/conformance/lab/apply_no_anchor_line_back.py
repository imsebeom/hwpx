"""개발용: HWPX 에서 다음 문단이 행 나눔 표 앵커일 때 쪽 끝 문단을 한 줄 덜 담는 규칙을 끈다.

    python apply_no_anchor_line_back.py [--revert]

typeset 은 문단을 쪽 끝에서 나눌 때 다음 문단이 자리 차지 행 나눔 표의 앵커면 한 줄을 되돌려 다음 쪽으로 넘긴다(네이티브 HWP 근거).
한/글 새 조판 d075 6쪽: p16(3줄, 다음 p17 은 자리 차지 CELL 표 앵커)을 2줄 | 1줄로 나누는데, 엔진은 이 규칙으로 1줄 | 2줄로 나눴다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx no-anchor-line-back]"

EDITS = [
    (
        "renderer/typeset.rs",
        "            if cursor_line == 0\n"
        "                && end_line > cursor_line + 1\n"
        "                && end_line < line_count\n"
        "                && next_para_is_rowbreak_anchor_table\n",
        "            if cursor_line == 0\n"
        "                && end_line > cursor_line + 1\n"
        "                && end_line < line_count\n"
        "                && next_para_is_rowbreak_anchor_table\n"
        f"                // {TAG} HWPX 는 한 줄을 되돌리지 않는다(d075 6쪽: 한/글 2줄 | 1줄)\n"
        "                && !st.profile.hwpx_container()\n",
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
