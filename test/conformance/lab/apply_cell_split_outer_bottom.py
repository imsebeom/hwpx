"""개발용: HWPX 의 CELL(셀 단위로 나눔) 표를 쪽 끝에서 행 안으로 자를 때 표 바깥 여백 아래만큼 자리를 남긴다.

    python apply_cell_split_outer_bottom.py [--revert]

근거(2026-10-18 한/글 실험 exp/make_outmargin243.py): d243 둘째 표(CELL, 바깥 여백 141)의 바깥 여백 아래를 0, 141, 283, 425 로
바꾸고 세로 위치를 옮기면, 교사 칸이 4번째 줄을 넘기는 위치가 여백 변화량만큼(1배) 옮겨 간다(offset 900~950, 768~778,
600~650, 450~500). issue1949 표본(바깥 여백 283)도 여백 아래를 0 으로 하면 1쪽에 한 줄을 더 담는다(exp/make_reserve1949.py).
두 실험 모두 행 안을 자르는 경우다. 행 경계 판정(행을 통째로 담을지)까지 줄이면 d160, d204, d251, d279 가 한 쪽씩
늘어(d279 는 바깥 여백 아래 850 으로 행 2 가 0.2px 차이로 밀림) 행 안 자르기 예산에서만 뺀다. 엔진의 HWPX CELL 은 RowBreak 다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx cell-split-outer-bottom]"

EDITS = [
    (
        "renderer/typeset.rs",
        "            let mut budget = (avail_for_rows - consumed - cs_before - padding).max(0.0);\n",
        f"            // {TAG} HWPX CELL 표를 쪽 끝에서 행 안으로 자를 때 한/글은 바깥 여백 아래를 남긴다(d243 실험: 여백 변화량만큼 경계 이동)\n"
        "            let claude_outer_bottom = if st.profile.hwpx_container()\n"
        "                && !table.common.treat_as_char\n"
        "                && matches!(\n"
        "                    table.page_break,\n"
        "                    crate::model::table::TablePageBreak::RowBreak\n"
        "                ) {\n"
        "                hwpunit_to_px(table.outer_margin_bottom as i32, self.dpi)\n"
        "            } else {\n"
        "                0.0\n"
        "            };\n"
        "            let mut budget =\n"
        "                (avail_for_rows - consumed - cs_before - padding - claude_outer_bottom).max(0.0);\n",
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
