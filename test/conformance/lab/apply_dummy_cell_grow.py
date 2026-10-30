"""개발용: 칸 문단 줄 위치가 모두 0 인 더미 줄 배치 칸이 있는 글자처럼 취급 표는 tac-no-shrink-hwpx 넷째 조각(선언으로 행 안 키움)에서 뺀다.

    python apply_dummy_cell_grow.py [--revert]

근거(회귀 모음 「서식2_지원학생신청서」 c52, c54): 바깥 글자처럼 취급 표 안 1×1 표(sz 9282, 칸 6635)의 칸 문단 다섯이 모두 vertpos 0 인
생성기 더미 줄 배치다. 한/글은 열 때 다시 조판해 표를 크게 그리는데, 넷째 조각이 선언으로 행을 키우지 않아 8쪽 뒤 글이 26px 더 위로
올라갔다(한/글과 2pt 넘는 줄 78 → 83). 결과보고서 161번 표(에디터 저장본, 줄 배치 정상)는 대상이 아니다.
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
            "        if table.common.treat_as_char && self.profile.get().hwpx_container() && !claude_dummy_cells {\n"
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
