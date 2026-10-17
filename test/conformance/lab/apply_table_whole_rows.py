"""개발용: 「표 나눔」(HWPX pageBreak="TABLE", 엔진 CellBreak) 표는 쪽 첫 행이 아니면 행 안에서 자르지 않고 그 행부터 다음 쪽으로 넘긴다.

    python apply_table_whole_rows.py [--revert]

근거: REA hwpx_lab 실측(h4_float_table: TABLE 은 행 경계에서만 나뉘고 모든 행이 온전), 정답본 집계 harvest_tblsplit.py
(쪽을 넘는 TABLE 표 12건 중 10건이 첫 조각 높이 = 행 높이 누적합. 나머지 2건은 칸 안 표가 든 행이라 높이 추정이 어긋남).
엔진은 TABLE 을 CellBreak 로 읽어 쪽 끝 행을 칸 안에서 갈랐다(d124 p50 12,264 높이 행 → 한/글 6쪽, rhwp 5쪽).
쪽 첫 행이 쪽보다 크면 종전대로 자른다(넘겨도 들어갈 데가 없다).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx table-whole-rows]"

EDITS = [
    (
        "renderer/typeset.rs",
        "            let splittable = can_intra_split\n                && (mt.is_row_splittable(r) || native_short_parent_child_splittable);\n",
        "            let splittable = can_intra_split\n                && (mt.is_row_splittable(r) || native_short_parent_child_splittable)\n"
        f"                // {TAG} 「표 나눔」(CellBreak) 표는 쪽 첫 행이 아니면 행을 통째로 다음 쪽에 넘긴다(한/글 2024 실측)\n"
        "                && !(matches!(table.page_break, crate::model::table::TablePageBreak::CellBreak) && r > cursor_row);\n",
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
