"""개발용: 쪽을 넘는 표에서 자르는 행에서 시작하는 병합 칸(rowSpan > 1)도 높이로 잘라 그린다.

    python apply_rowspan_cut_row.py [--revert]

근거(d243 한/글 PDF 대 rhwp SVG): 2~5행에 걸친 칸을 rhwp 는 1쪽에서 자르지 않고 쪽 아래로 822pt 까지 넘쳐 그린 뒤 2쪽에 처음부터
다시 그렸다. 한/글은 줄 단위로 갈라 1쪽 750pt 까지 담고 2쪽에서 이어 간다.
원인: 행 단위 자름 표(start_cut/end_cut)는 그 행의 한 행 칸(rowSpan 1)만 담는데, 블록 분할이 아닌 조각은 자르는 행에서 시작하는
병합 칸에도 그 표를 「행 안 칸 순번」으로 찾아 썼다. 순번이 표 밖이면 「끝까지」(넘침, 다음 쪽 처음부터), 안이면 남의 칸 값을 받았다.
조각 경계에 걸친 병합 칸을 높이로 자르는 경로(#1748)는 칸이 조각 시작 행보다 위에서 시작할 때만 켜졌다.
처방: 블록 분할이 아닌 조각의 행 단위 자름은 한 행 칸에만 쓰고, 자르는 행에서 시작하는 병합 칸은 높이 경로로 보낸다
(다음 쪽에서는 그 행의 앞 조각 높이만큼 건너뛴다).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx rowspan-cut-row]"
TP = "renderer/layout/table_partial.rs"

EDITS = [
    (
        TP,
        "            } else {\n                !start_cut.is_empty() && cell_row == start_row\n            };\n            let is_split_end_row = if is_block_split {\n                split_end_block.is_some_and(|(s, e)| cell_row < e && cell_end_row > s)\n            } else {\n                !end_cut.is_empty() && cell_row == end_row.saturating_sub(1)\n            };\n            let is_in_split_row = is_split_start_row || is_split_end_row;\n            // [#5946]",
        "            } else {\n"
        f"                // {TAG} 행 단위 자름 표는 그 행의 한 행 칸만 담는다. 병합 칸은 아래 높이 경로가 맡는다\n"
        "                !start_cut.is_empty() && cell_row == start_row && cell.row_span == 1\n"
        "            };\n            let is_split_end_row = if is_block_split {\n                split_end_block.is_some_and(|(s, e)| cell_row < e && cell_end_row > s)\n            } else {\n"
        "                !end_cut.is_empty() && cell_row == end_row.saturating_sub(1) && cell.row_span == 1\n"
        "            };\n            let is_in_split_row = is_split_start_row || is_split_end_row;\n            // [#5946]",
    ),
    (
        TP,
        "            let straddles_fragment_start = cell_row < start_row && cell_end_row > start_row;\n            let straddles_fragment_end",
        "            let straddles_fragment_start = (cell_row < start_row && cell_end_row > start_row)\n"
        f"                // {TAG} 자르는 행(조각 시작 행)에서 시작하는 병합 칸도 앞 조각에 일부를 그렸다\n"
        "                || (!is_block_split\n"
        "                    && cell.row_span > 1\n"
        "                    && cell_row == start_row\n"
        "                    && !start_cut.is_empty());\n"
        "            let straddles_fragment_end",
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
