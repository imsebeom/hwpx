"""개발용: HWPX 표의 칸 간격(cellSpacing)은 행 사이뿐 아니라 표 위아래 끝에도 둔다(세로만).

    python apply_cellspacing_edge.py [--revert]

근거(결과보고서 18쪽 124번 표, cellSpacing 300, 4행): 한/글 표 높이 18512 = 행 합 17012 + 간격 300 × 5(위 끝, 행 사이 셋, 아래 끝). 폭도
칸 합 43972 + 300 × 5 = 45472 로 네 변 모두 간격이 있다. 엔진은 행 사이(3번)만 세어 표를 600 작게 재고(열 때 다시 재기가 17912), 행을 위 끝에
붙여 그려 마지막 사진 설명 줄이 4px 위였다. 가로는 이번에 바꾸지 않는다.
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx cellspacing-edge]"

ROWY_OLD = (
    "        let mut row_y = vec![0.0f64; row_count + 1];\n"
    "        for i in 0..row_count {\n"
    "            row_y[i + 1] =\n"
    "                row_y[i] + row_heights[i] + if i + 1 < row_count { cell_spacing } else { 0.0 };\n"
    "        }\n"
)
ROWY_NEW = (
    "        let mut row_y = vec![0.0f64; row_count + 1];\n"
    f"        // {TAG} HWPX 는 칸 간격을 표 위아래 끝에도 둔다(결과보고서 124번 표: 높이 = 행 합 + 간격 × (행 수 + 1))\n"
    "        let claude_edge = self.profile.get().hwpx_container() && cell_spacing > 0.0;\n"
    "        if claude_edge {\n"
    "            row_y[0] = cell_spacing;\n"
    "        }\n"
    "        for i in 0..row_count {\n"
    "            row_y[i + 1] = row_y[i]\n"
    "                + row_heights[i]\n"
    "                + if i + 1 < row_count || claude_edge { cell_spacing } else { 0.0 };\n"
    "        }\n"
)

EDITS = [
    ("renderer/layout/table_layout.rs", ROWY_OLD, ROWY_NEW),
    (
        "renderer/height_measurer.rs",
        (
            "        let raw_table_height: f64 =\n"
            "            row_heights.iter().sum::<f64>() + cell_spacing * (row_count.saturating_sub(1) as f64);\n"
        ),
        (
            "        let raw_table_height: f64 =\n"
            "            row_heights.iter().sum::<f64>() + cell_spacing * (row_count.saturating_sub(1) as f64)\n"
            f"            // {TAG} HWPX 는 칸 간격을 표 위아래 끝에도 둔다\n"
            "                + if !self.is_native_hwp5 && !self.is_hwp3_variant { cell_spacing * 2.0 } else { 0.0 };\n"
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
