"""개발용: 행 안 자르기 여백(row_remaining_visible_padding_height)도 내용이 선언 높이를 넘는 칸에서는 줄이지 않은 여백을 쓴다.

    python apply_cut_pad_unscaled.py [--revert]

근거(2026-10-18 issue1949 표본): 거대 칸의 선언 높이가 282 로 위아래 여백 합(141 + 141)과 같아 Task #501 방어가 여백을
절반(141)으로 줄였다. 행은 내용으로 수만 HU 까지 늘어나므로 한/글은 원래 여백을 쓴다(no-ls-row-pad 가 행 높이 측정에
넣은 것과 같은 규칙). 여백을 줄인 채 자르면 1쪽 예산이 141 HU 후해, 한/글이 37줄을 두는 자리(아래 여백을 줄여 보면
200~250 HU 를 더 줘야 38줄)에 38줄을 담았다(exp/make_bottommargin.py, make_edit1949.py: 편집 뒤에도 한/글 37줄).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx cut-pad-unscaled]"

EDITS = [
    (
        "renderer/layout/table_layout.rs",
        "            let (_, _, pad_top, pad_bottom) = self.resolve_cell_padding(cell, table);\n"
        "            max_padding = max_padding.max(pad_top + pad_bottom);\n",
        "            let (_, _, pad_top, pad_bottom) = self.resolve_cell_padding(cell, table);\n"
        f"            // {TAG} 선언 높이가 여백뿐이라 여백을 줄인 칸도 남은 내용이 선언을 넘으면 한/글은 원래 여백을 쓴다(issue1949 거대 칸)\n"
        "            let (pad_top, pad_bottom) = if self.profile.get().hwpx_container() && cell.height < 0x8000_0000 {\n"
        "                let decl_h = hwpunit_to_px(cell.height as i32, self.dpi);\n"
        "                let (_, _, raw_top, raw_bottom) = self.claude_cell_padding_unscaled(cell, table);\n"
        "                let rest: f64 = units[su..].iter().map(|unit| unit.height).sum();\n"
        "                if rest > decl_h\n"
        "                    && crate::model::table::Cell::vertical_padding_is_abnormal(decl_h, raw_top + raw_bottom)\n"
        "                {\n"
        "                    (raw_top, raw_bottom)\n"
        "                } else {\n"
        "                    (pad_top, pad_bottom)\n"
        "                }\n"
        "            } else {\n"
        "                (pad_top, pad_bottom)\n"
        "            };\n"
        "            max_padding = max_padding.max(pad_top + pad_bottom);\n",
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
