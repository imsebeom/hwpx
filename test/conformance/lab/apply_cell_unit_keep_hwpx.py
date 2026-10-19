"""개발용: HWPX 셀 단위 나눔(CELL = 엔진 RowBreak) 표의 행 안 자르기에서, 완결된 줄이 하나라도 있으면 25px 고아 가드를 걸지 않는다.

    python apply_cell_unit_keep_hwpx.py [--revert]

#6035 는 저장 줄 배치에 「쪽 경계에서 줄 단위로 나눈 흔적」이 있을 때만 고아 가드를 풀었다. 한/글 새 조판(흔적 없음) d189 1쪽: 4x3 CELL 표
머리 행 아래 남은 27.4px 에 둘째 행 첫 줄(칸마다 한 줄, 내용 16.9px)을 남기고 자른다. 엔진은 16.9 < 25px 라 행을 통째로 넘겼다.
저장 줄 배치가 있는 문서는 #6035 저장 흔적 판정에 맡긴다(같이 풀면 저장 줄 d189 2쪽이 50pt 어긋남).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx cell-unit-keep-hwpx]"

EDITS = [
    (
        "renderer/typeset.rs",
        "                && res.end_cut.iter().any(|units| *units > 0)\n"
        "                && row_has_stored_same_vpos_split_signal(table, r);\n",
        "                && res.end_cut.iter().any(|units| *units > 0)\n"
        f"                // {TAG} 줄 배치 없는 HWPX 는 저장 흔적이 없어도 완결 줄 하나면 남긴다(한/글 새 조판 d189 p9 둘째 행 첫 줄 16.9px)\n"
        "                && (row_has_stored_same_vpos_split_signal(table, r)\n"
        "                    || (st.profile.hwpx_container()\n"
        "                        && table.cells.iter().filter(|c| c.row as usize == r).all(|c| {\n"
        "                            c.paragraphs.iter().all(|p| {\n"
        "                                p.line_segs.iter().all(|s| {\n"
        "                                    s.tag & crate::model::paragraph::LineSeg::TAG_IMPLEMENTATION_PROPERTY != 0\n"
        "                                })\n"
        "                            })\n"
        "                        })));\n",
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
