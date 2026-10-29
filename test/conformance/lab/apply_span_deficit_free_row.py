"""개발용: HWPX 병합 칸 내용이 걸친 행 합보다 크면(2-c) 부족분을 「걸친 행 중 한 행 칸이 없는 마지막 행」에 붙인다(없으면 종전대로 마지막 행).

    python apply_span_deficit_free_row.py [--revert]

근거(결과보고서 29, 30쪽 163, 164번 표): 10~11행에 걸친 칸(c0)의 부족분을 마지막 행(11행)에 붙여 11행이 3132 가 됐다. 11행에는 그림 설명 칸
(한 행 칸, 필요 2354)이 있어, 세로 가운데 정렬 글이 한/글보다 4px 아래였다. 10행은 병합 칸에만 걸친 행이라 한/글은 부족분을 그쪽에 둔다.
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx span-deficit-free-row]"

EDITS = [
    (
        "renderer/height_measurer.rs",
        (
            "                if required_height > combined {\n"
            "                    let deficit = required_height - combined;\n"
            "                    row_heights[r + span - 1] += deficit;\n"
            "                }\n"
        ),
        (
            "                if required_height > combined {\n"
            "                    let deficit = required_height - combined;\n"
            f"                    // {TAG} HWPX 는 한 행 칸이 없는 걸친 행(병합 칸에만 걸친 행)이 부족분을 받는다(결과보고서 163번 표 10행)\n"
            "                    let target = if !self.is_native_hwp5 && !self.is_hwp3_variant {\n"
            "                        (r..r + span)\n"
            "                            .rev()\n"
            "                            .find(|&i| !table.cells.iter().any(|c| c.row as usize == i && c.row_span == 1))\n"
            "                            .unwrap_or(r + span - 1)\n"
            "                    } else {\n"
            "                        r + span - 1\n"
            "                    };\n"
            "                    row_heights[target] += deficit;\n"
            "                }\n"
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
