"""개발용: HWPX 다행 행 나눔 표의 「저장 틀」(saved_rowbreak_object_frame)은 잰 표 높이가 적힌 높이 안에 들 때만 쓴다.

    python apply_rowbreak_frame_fit.py [--revert]

근거(정답본 d022, 한/글 재저장본 그대로 열기): 71행 표(쪽 나눔 칸, 적힌 높이 44931 = 599px, 잰 높이 2272px)를 한/글은 1~3쪽에
나눠 그린다. 엔진은 다음 문단이 새 쪽에서 시작한다는 이유로 이 규칙을 써 표를 599px 틀 하나로 1쪽에 놓고 나머지 행을 잇지 않아
1쪽 아래로 잘리고 3쪽 문서가 됐다(한/글 5쪽).
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx rowbreak-frame-fit]"

EDITS = [
    (
        "renderer/typeset.rs",
        (
            "            && next_starts_new_page\n"
            "            && !rowbreak_table_has_internal_saved_vpos_reset(table))\n"
        ),
        (
            "            && next_starts_new_page\n"
            "            && !rowbreak_table_has_internal_saved_vpos_reset(table)\n"
            f"            // {TAG} 잰 표가 적힌 높이(첫 조각) 안에 들 때만 — 더 크면 행을 다음 쪽으로 이어야 한다(d022 71행: 적힌 599px, 잰 2272px)\n"
            "            && table_total - host_spacing_total <= declared_object_total - host_spacing_total + 1.0)\n"
        ),
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
