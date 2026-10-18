"""개발용: HWPX 표 행을 쪽 끝에서 칸 안에서 자를 때 마지막으로 담는 줄의 뒤 줄 간격은 남은 자리에 넣지 않는다.

    python apply_cell_cut_trailing_spacing.py [--revert]

근거(2026-10-18 정답본 d243 표 2 행 2, 한/글 저장 줄 기록): 행이 908.8px 에서 시작해 본문 바닥까지 7530 HU 가 남았다.
교사 칸(여백 566+566, 줄 1000+600)은 4줄(vpos 0..4800, 다음 줄은 다음 쪽 0)을 담는다. 4줄 + 마지막 줄 간격이면
566 + 6400 + 566 = 7532 로 넘치고, 마지막 줄 간격을 빼면 6932 로 들어간다. 자료 칸(줄 900+540)도 5줄(7226)까지 담고
6줄(8666)은 넘긴다. 엔진은 유닛 높이(줄 + 간격) 전체로 따져 교사 칸을 3줄만 담았다. 본문 줄과 CELL 행 통째 판정
(row-visible-fit)과 같은 「마지막 줄 간격은 넘쳐도 된다」 규칙이다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx cell-cut-trailing-spacing]"

EDITS = [
    (
        "renderer/layout/table_layout.rs",
        "                    let nested_atom_tail = self.nested_atom_invisible_tail(cell, u, styles);\n"
        "                    if nested_atom_tail > 0.0 && h + u.height - nested_atom_tail <= avail_height {\n",
        f"                    // {TAG} 마지막으로 담는 줄의 뒤 줄 간격은 쪽 끝을 넘어도 된다(d243: 한/글이 교사 칸 4줄을 담는다)\n"
        "                    if self.profile.get().hwpx_container()\n"
        "                        && !u.empty_spacer\n"
        "                        && u.nested_row.is_none()\n"
        "                        && u.nested_table_fragment.is_none()\n"
        "                        && u.vis_end == u.vis_start + 1\n"
        "                        // 칸의 마지막 줄 유닛은 높이에 줄 간격이 없다(d191, d014 에서 두 번 빼 행이 들어간다고 오판)\n"
        "                        && j + 1 < units.len()\n"
        "                    {\n"
        "                        let claude_tail = cell\n"
        "                            .paragraphs\n"
        "                            .get(u.para_idx)\n"
        "                            .and_then(|p| p.line_segs.get(u.vis_start))\n"
        "                            .map(|s| hwpunit_to_px(s.line_spacing.max(0), self.dpi))\n"
        "                            .unwrap_or(0.0)\n"
        "                            .min(u.height);\n"
        "                        if claude_tail > 0.0\n"
        "                            && h + u.height - claude_tail <= avail_height + ROW_CUT_CAPACITY_FP_EPSILON_PX\n"
        "                        {\n"
        "                            h += u.height - claude_tail;\n"
        "                            j += 1;\n"
        "                            break;\n"
        "                        }\n"
        "                    }\n"
        "                    let nested_atom_tail = self.nested_atom_invisible_tail(cell, u, styles);\n"
        "                    if nested_atom_tail > 0.0 && h + u.height - nested_atom_tail <= avail_height {\n",
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
