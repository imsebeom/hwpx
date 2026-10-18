"""개발용: #2400 시험(issue1949 HWPX 표본)의 재현점을 partial-omtop-hwpx 뒤 첫 조각 하단에 맞춘다.

    python apply_test_1949_omtop.py [--revert]

partial-omtop-hwpx 로 HWPX 표본의 첫 조각이 바깥 위 여백 283(3.8px)만큼 내려가 하단이 1062.9 → 1066.7 이 됐다. 한/글 PDF 와 1쪽 글줄이
0.4pt 안으로 맞는다(첫 줄 71.1 대 71.0, 「제1장 선체구조」 119.3 대 119.7). 시험의 전제(재현점이 첫 조각 하단 5px 안)를 그대로 두고 값만 옮긴다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx test-1949-omtop]"

EDITS = [
    (
        "wasm_api/tests.rs",
        '        let click_y = if path.ends_with(".hwpx") { 1059.2 } else { 1057.3 };\n',
        f"        // {TAG} partial-omtop-hwpx 로 HWPX 첫 조각이 바깥 위 여백 283(3.8px)만큼 더 내려간다(하단 1066.7, 한/글 PDF 와 0.4pt 안)\n"
        '        let click_y = if path.ends_with(".hwpx") { 1063.0 } else { 1057.3 };\n',
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
