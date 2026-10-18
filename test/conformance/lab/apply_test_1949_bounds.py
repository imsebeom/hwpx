"""개발용: #2214 시험의 1쪽 칸 조각 높이 고정값을 HWPX 표본에서 947.8 로 고친다(cut-row-pad-stored, cut-pad-unscaled 뒤).

    python apply_test_1949_bounds.py [--revert]

issue1949 거대 칸은 선언 높이 282 가 여백 합(141 + 141)과 같아 여백을 절반으로 줄여 왔다. 한/글 PDF 의 머리 행 간격 1486 HU 가
원래 여백(1200 + 141 + 141 = 1482)과 맞아 HWPX 에서는 원래 여백을 쓰니, 1쪽 조각이 아래 여백 1.9px 만큼 길어진다
(945.9 -> 947.8). 1쪽 자르기(37줄)는 한/글 편집 사본(make_edit1949.py)과 같다. HWP 표본은 그대로 945.9.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx cut-row-pad-stored]"

EDITS = [
    (
        "wasm_api/tests.rs",
        "        assert!(\n"
        "            (transient_bounds_h - 945.9).abs() <= 0.2,\n"
        '            "{label}: transient bounds h={transient_bounds_h}"\n'
        "        );\n"
        "        assert!(\n"
        "            (flushed_bounds_h - 945.9).abs() <= 0.2,\n"
        '            "{label}: flushed bounds h={flushed_bounds_h}"\n'
        "        );\n",
        f"        // {TAG} HWPX 는 선언 높이가 여백뿐인 거대 칸도 원래 여백(141 + 141)을 쓴다(한/글 PDF 머리 행 간격 1486 HU)\n"
        '        let expected_bounds_h = if label == "hwpx" { 947.8 } else { 945.9 };\n'
        "        assert!(\n"
        "            (transient_bounds_h - expected_bounds_h).abs() <= 0.2,\n"
        '            "{label}: transient bounds h={transient_bounds_h}"\n'
        "        );\n"
        "        assert!(\n"
        "            (flushed_bounds_h - expected_bounds_h).abs() <= 0.2,\n"
        '            "{label}: flushed bounds h={flushed_bounds_h}"\n'
        "        );\n",
    ),
    (
        "wasm_api/tests.rs",
        "        let click_y = 1057.3;\n",
        f"        // {TAG} HWPX 첫 조각은 아래 여백 141(1.9px)만큼 길어 재현점도 그만큼 내려간다(1061.0 -> 1062.9)\n"
        '        let click_y = if path.ends_with(".hwpx") { 1059.2 } else { 1057.3 };\n',
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
