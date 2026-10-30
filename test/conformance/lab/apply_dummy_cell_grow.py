"""개발용: tac-no-shrink-hwpx 넷째 조각(HWPX 글자처럼 취급 표는 선언 표 높이로 행을 키우지 않음)에서 두 경우는 빼고 종전처럼 키운다.

    python apply_dummy_cell_grow.py [--revert]

1) 칸 문단 줄 위치가 모두 0 인 더미 줄 배치(생성기) 칸이 있는 표. 근거: 회귀 모음 「서식2_지원학생신청서」 c52, c54 의 칸 안 1×1 표
   (sz 9282, 칸 6635, 칸 문단 다섯이 모두 vertpos 0). 한/글은 열 때 다시 조판해 크게 그리는데 키우지 않아 8쪽 뒤 글이 26px 더 올라갔다.
2) 칸 높이 선언이 내용과 맞는 표 — 모든 열의 칸 높이 합이 같고 엔진이 잰 행 합도 그와 같을 때. 그때 표 높이가 그보다 큰 몫은 한/글이
   그리는 몫이다. 근거: 회귀 모음 「연구대회 관련 Q_A」 c22 2행 표(sz 7704, 칸 합 7604, 행 합 7604 → 한/글 마지막 행 +100).
   넷째 조각이 막던 결과보고서 표 7개(161번 등)는 행 합이 칸 합보다 크거나(선언이 낡음) 열마다 칸 합이 달라 대상이 아니다.
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx dummy-cell-grow]"

EDITS = [
    (
        "renderer/layout/table_layout.rs",
        "        if table.common.treat_as_char && self.profile.get().hwpx_container() {\n            return;\n        }\n        let target_height = if table.common.height > 0 {\n",
        (
            f"        // {TAG} 칸 문단 줄 위치가 모두 0 인 더미 줄 배치(생성기) 칸이 있으면 선언대로 키운다(서식2 c52 1×1 표: 한/글이 크게 그림)\n"
            "        let claude_dummy_cells = table.cells.iter().any(|c| {\n"
            "            c.paragraphs.len() >= 2\n"
            "                && c.paragraphs.iter().all(|p| p.line_segs.first().is_some_and(|s| s.vertical_pos == 0))\n"
            "        });\n"
            "        // 칸 선언이 내용과 맞으면(모든 열 칸 높이 합이 같고 행 합도 같음) 표 높이가 그보다 큰 몫은 한/글이 그린다(c22: 7704 > 7604)\n"
            "        let claude_decl_consistent = {\n"
            "            let ncol = table.cells.iter().map(|c| c.col as usize + c.col_span as usize).max().unwrap_or(0);\n"
            "            let sums: Vec<i64> = (0..ncol)\n"
            "                .map(|k| {\n"
            "                    table\n"
            "                        .cells\n"
            "                        .iter()\n"
            "                        .filter(|c| (c.col as usize) <= k && k < c.col as usize + c.col_span as usize)\n"
            "                        .map(|c| i64::from(c.height.min(i32::MAX as u32)))\n"
            "                        .sum()\n"
            "                })\n"
            "                .collect();\n"
            "            let rows_hu = i64::from(crate::renderer::px_to_hwpunit(row_heights.iter().sum::<f64>(), self.dpi));\n"
            "            !sums.is_empty() && sums.iter().all(|s| *s == sums[0]) && (rows_hu - sums[0]).abs() <= 75\n"
            "        };\n"
            "        if table.common.treat_as_char && self.profile.get().hwpx_container() && !claude_dummy_cells && !claude_decl_consistent {\n"
            "            return;\n"
            "        }\n"
            "        let target_height = if table.common.height > 0 {\n"
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
