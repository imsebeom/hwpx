"""개발용: 셀 영역(cellzone) 배경과 대각선을 끝 칸의 병합 범위 끝까지 그린다.

    python apply_cellzone_span.py [--revert]

근거(d130 사본 실험, scratchpad make_zone.py → hwpx_lab/measure.py): 머리 띠 표의 칸 (0,0) 이 colSpan 2 이고
셀 영역 끝 주소가 (0,0) 이면 한/글 2024 PDF 는 그라데이션을 표 전체 폭(두 열)에 칠한다. 엔진은 첫 열 끝(155.6px)에서 멈췄다.
끝 주소를 가려진 칸 (0,1) 로 바꾸면 한/글은 셀 영역을 버린다(PDF 에 칠하지 않고, 다시 저장한 파일에서도 사라짐).
셀 영역 끝 주소는 그리드 좌표가 아니라 칸 주소다. 이음오피스(pblsketch/openoffice) 패치 0009 가 같은 결함을 보고했다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx cellzone-span]"

EDITS = [
    (
        "renderer/layout/table_layout.rs",
        "                // zone 영역의 좌표 계산\n"
        "                let sc = zone.start_col as usize;\n"
        "                let ec = (zone.end_col as usize + 1).min(col_count);\n"
        "                let sr = zone.start_row as usize;\n"
        "                let er = (zone.end_row as usize + 1).min(row_count);\n",
        "                // zone 영역의 좌표 계산\n"
        f"                // {TAG} 끝 주소는 칸 주소다. 끝 칸이 병합 칸이면 그 범위 끝까지 칠하고,\n"
        "                // 끝 주소가 가려진 칸이면 한/글처럼 셀 영역을 쓰지 않는다(d130 사본 실험).\n"
        "                let Some(end_cell) = table.cells.iter().find(|c| {\n"
        "                    c.row == zone.end_row && c.col == zone.end_col\n"
        "                }) else {\n"
        "                    continue;\n"
        "                };\n"
        "                let sc = zone.start_col as usize;\n"
        "                let ec = (end_cell.col as usize + (end_cell.col_span as usize).max(1)).min(col_count);\n"
        "                let sr = zone.start_row as usize;\n"
        "                let er = (end_cell.row as usize + (end_cell.row_span as usize).max(1)).min(row_count);\n",
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
