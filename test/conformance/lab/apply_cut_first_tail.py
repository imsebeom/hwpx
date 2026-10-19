"""개발용: HWPX 칸 행 안 자르기에서 조각의 첫 줄도 뒤 줄 간격은 쪽 끝을 넘어도 되게 한다.

    python apply_cut_first_tail.py [--revert]

cell-cut-trailing-spacing(d243)은 마지막으로 담는 줄의 뒤 줄 간격을 쪽 끝 밖으로 허용하는데, 조각의 첫 유닛(j == start)은 그 판정을
지나지 않고 늘 통째(줄 간격 포함)로 담겨, 호출 쪽이 예산과 견줘 행을 통째로 다음 쪽에 넘겼다. 한/글 새 조판 d042 1쪽: 행 2 (칸 여백
142, 줄 1000 + 간격 300)를 987.9 에서 시작해 첫 줄만 담고 자른다(괘선 1006.7, 본문 바닥 1009.1). 엔진은 첫 줄 소비 17.3 > 예산 16.5 로
행을 넘겨 2쪽 전체가 17.2px 아래였다(합성 vpos 는 한/글과 HU 까지 같아 남은 자리 1512 도 같다). 칸의 마지막 줄이 아니고 줄 간격을 빼면
들어갈 때 그 줄까지 담고 멈춘다. 단 여러 행에 걸친 칸이 이 행에서 시작하면 한/글은 넘긴다(d139 행 7, ⓓ 칸 rowSpan 3). 앞 행에서 시작해
걸친 칸은 상관없다(d200 행 16 은 담는다, d143, d238 같은 문서).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx cut-first-tail]"

# advance_row_cut_inner 의 자리(advance_row_block_cut 에도 같은 줄이 있어 다음 진단 줄까지 넣어 가른다)
ANCHOR = (
    "                if j > start && h + u.height > avail_height + ROW_CUT_CAPACITY_FP_EPSILON_PX {\n"
    '                    if std::env::var("RHWP_DIAG_6368").is_ok() {\n'
    "                        let over = h + u.height - avail_height;\n"
    "                        if over <= 2.0 {\n"
    "                            eprintln!(\n"
    '                                "DIAG_6368 cap-cut'
)

EDITS = [
    (
        "renderer/layout/table_layout.rs",
        ANCHOR,
        f"                // {TAG} 조각의 첫 줄도 뒤 줄 간격만 넘치면 담고 멈춘다(d042 1쪽 행 2 첫 줄)\n"
        "                if j == start\n"
        "                    && self.profile.get().hwpx_container()\n"
        "                    && h + u.height > avail_height + ROW_CUT_CAPACITY_FP_EPSILON_PX\n"
        "                    && !u.empty_spacer\n"
        "                    && u.nested_row.is_none()\n"
        "                    && u.nested_table_fragment.is_none()\n"
        "                    && u.vis_end == u.vis_start + 1\n"
        "                    && j + 1 < units.len()\n"
        "                    // 여러 행에 걸친 칸이 이 행에서 시작하면 한/글은 넘긴다(d139 행 7: ⓓ 칸 rowSpan 3 시작, 예산 16.2).\n"
        "                    // 앞 행에서 시작해 이 행에 걸친 칸은 상관없다(d200 행 16 은 담는다)\n"
        "                    && !table\n"
        "                        .cells\n"
        "                        .iter()\n"
        "                        .any(|c| c.row_span > 1 && c.row as usize == row)\n"
        "                {\n"
        "                    let claude_tail = cell\n"
        "                        .paragraphs\n"
        "                        .get(u.para_idx)\n"
        "                        .and_then(|p| p.line_segs.get(u.vis_start))\n"
        "                        .map(|s| hwpunit_to_px(s.line_spacing.max(0), self.dpi))\n"
        "                        .unwrap_or(0.0)\n"
        "                        .min(u.height);\n"
        "                    if claude_tail > 0.0\n"
        "                        && h + u.height - claude_tail <= avail_height + ROW_CUT_CAPACITY_FP_EPSILON_PX\n"
        "                    {\n"
        "                        h += u.height - claude_tail;\n"
        "                        j += 1;\n"
        "                        break;\n"
        "                    }\n"
        "                }\n" + ANCHOR,
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
