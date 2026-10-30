"""개발용: 칸 안 어울림 그림이 오른쪽에 있어 줄 시작이 0 인 저장 줄도 저장 폭을 쓴다(HWPX).

    python apply_cell_square_right.py [--revert]

근거(「채점기준표검토의견_김경선교수_261028」 자료 1 칸): 오른쪽 어울림 그림 옆 세 문단의 저장 줄이 모두 폭 21657 인데, 그림을 품지 않은
둘째, 셋째 문단이 칸 전체 폭으로 양쪽 정렬되어 그림과 겹쳤다. #5818 조건이 column_start > 0(왼쪽 그림)만 보았다.
문단 자체 여백으로 좁은 줄을 오인하지 않게 여백을 뺀 폭이 1200 넘게 모자랄 때만 쓴다.
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx cell-square-right]"

EDITS = [
    (
        "renderer/layout/paragraph_layout.rs",
        (
            "                && self.cell_has_square_float.get()\n"
            "                && comp_line.column_start > 0\n"
            "                && comp_line.segment_width > 0\n"
            "                && comp_line.segment_width < col_area_w_hu;\n"
        ),
        (
            "                && self.cell_has_square_float.get()\n"
            f"                // {TAG} 오른쪽 그림은 줄 시작이 0 이다 — 여백을 뺀 폭보다 1200 넘게 좁으면 그림 때문이다(자료 1 칸: 뒤 문단이 그림과 겹침)\n"
            "                && (comp_line.column_start > 0\n"
            "                    || (comp_line.segment_width\n"
            "                            < col_area_w_hu\n"
            "                                - crate::renderer::px_to_hwpunit(margin_left + margin_right, self.dpi)\n"
            "                                - 1200))\n"
            "                && comp_line.segment_width > 0\n"
            "                && comp_line.segment_width < col_area_w_hu;\n"
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
