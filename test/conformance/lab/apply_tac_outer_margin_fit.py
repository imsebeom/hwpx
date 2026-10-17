"""개발용: 블록처럼 다루는 글자처럼 취급 표(flowWithText=0)의 쪽 맞춤 판정에 표 바깥 여백 위아래를 더한다.

    python apply_tac_outer_margin_fit.py [--revert]

근거(d114 p31): 한/글은 이 표의 줄 높이를 「선언 높이 + 바깥 여백 위아래」(3263 + 139 + 139 = 3541)로 적고, 쪽 끝에서
그 줄 높이가 남은 높이를 넘으면 표를 다음 쪽으로 넘긴다. 엔진은 선언 높이(43.5px)만으로 맞춰 보아 남은 높이를 0.7px 넘는
표(47.2px)를 앞 쪽에 넣었다(3쪽 담은 높이 916.5px > 본문 895.8px, 한/글 13쪽 대 rhwp 15쪽).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx tac-outer-margin-fit]"

EDITS = [
    (
        "renderer/typeset.rs",
        "            && matches!(table.page_break, crate::model::table::TablePageBreak::None)\n"
        "            && ft.table_footnotes.is_empty()\n"
        "            && st.current_height + ft.effective_height <= available + 0.5;\n"
        "        let declared_fit_height = if hwpx_noninline_tac_measured_fit {\n"
        "            ft.effective_height\n"
        "        } else {\n",
        "            && matches!(table.page_break, crate::model::table::TablePageBreak::None)\n"
        "            && ft.table_footnotes.is_empty()\n"
        "            && st.current_height + ft.effective_height + claude_tac_outer_margin_px <= available + 0.5;\n"
        "        let declared_fit_height = if hwpx_noninline_tac_measured_fit {\n"
        "            ft.effective_height + claude_tac_outer_margin_px\n"
        "        } else {\n",
    ),
    (
        "renderer/typeset.rs",
        "        let hwpx_noninline_tac_measured_fit = self.profile.get().hwpx_stored_layout()\n",
        f"        // {TAG} 한/글은 이 표의 줄 높이를 선언 높이 + 바깥 여백 위아래로 잡고 쪽 끝 맞춤도 그 높이로 본다(d114 p31: 3263+139+139)\n"
        "        let claude_tac_outer_margin_px = hwpunit_to_px(\n"
        "            i32::from(table.outer_margin_top) + i32::from(table.outer_margin_bottom),\n"
        "            self.dpi,\n"
        "        );\n"
        "        let hwpx_noninline_tac_measured_fit = self.profile.get().hwpx_stored_layout()\n",
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
            sys.exit(f"{rel}: 자리 {n}곳 — {find[:50]!r}")
        s = s.replace(find, repl)
        f.write_bytes(s.replace("\n", nl).encode("utf-8"))
        print("넣음", rel)


if __name__ == "__main__":
    main()
