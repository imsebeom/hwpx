"""개발용: HWPX 표에서 병합 칸에만 걸친 행(한 행 칸이 없는 행)은 병합 칸 선언으로 풀어 0 이 되면 0 으로 둔다(기본값 400 으로 채우지 않음).

    python apply_zero_span_row.py [--revert]

근거(정답본 d120 50번 문단 예산표, 20행 5열): 병합 칸 선언(2-b)으로 행을 풀면 10행, 12행이 0 이 되고 행 합이 29572 로 한/글 표 높이 29573 과
같다. 엔진 3단계가 높이 0 인 행을 400(5.3px)으로 채워 표가 커졌고, 열 때 다시 재기(tac-restate-on-open)가 30696 으로 쟀다(d120 11 → 12쪽).
한 행 칸이 있는 행은 종전대로 둔다.
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx zero-span-row]"

EDITS = [
    (
        "renderer/height_measurer.rs",
        (
            "        // 3단계: 높이가 0인 행은 기본값 적용\n"
            "        for h in &mut row_heights {\n"
            "            if *h <= 0.0 {\n"
            "                *h = hwpunit_to_px(400, self.dpi);\n"
            "            }\n"
            "        }\n"
        ),
        (
            "        // 3단계: 높이가 0인 행은 기본값 적용\n"
            f"        // {TAG} HWPX 는 병합 칸에만 걸친 행(한 행 칸 없음)이 선언으로 0 이 되면 0 으로 둔다(d120 예산표: 한/글 행 합 = 표 높이)\n"
            "        let claude_hwpx = !self.is_native_hwp5 && !self.is_hwp3_variant;\n"
            "        for (r, h) in row_heights.iter_mut().enumerate() {\n"
            "            if *h <= 0.0 {\n"
            "                let span_only = claude_hwpx\n"
            "                    && !table.cells.iter().any(|c| c.row as usize == r && c.row_span == 1)\n"
            "                    && table.cells.iter().any(|c| {\n"
            "                        c.row_span > 1 && (c.row as usize) <= r && r < c.row as usize + c.row_span as usize\n"
            "                    });\n"
            "                if !span_only {\n"
            "                    *h = hwpunit_to_px(400, self.dpi);\n"
            "                }\n"
            "            }\n"
            "        }\n"
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
