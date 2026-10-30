"""개발용: 쪽 번호 컨트롤 뒤의 글자처럼 취급 표가 남은 자리보다 크면 다음 쪽으로 보낸다.

    python apply_pagenum_tac_break.py [--revert]

근거(강의일지 9개 c55~c64, 한/글 3쪽, 엔진 2쪽): 첫 문단이 쪽 번호 + 쪽 높이만 한 표면 한/글은 쪽 번호만 있는 1쪽을 남기고 표를 2쪽에 둔다.
사본 실험: 쪽 번호를 빼면 1쪽, 행을 줄이면 1쪽, 적힌 표 높이만 줄이면 그대로(잰 높이로 판단한다).
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx pagenum-tac-break]"

EDITS = [
    (
        "renderer/typeset.rs",
        (
            "            && !saved_tac_table_bottom_fits\n"
            "            && !st.current_items.is_empty())\n"
            "            || stored_vpos_rewind_break\n"
            "        {\n"
            "            st.advance_column_or_new_page();\n"
            "        }\n"
        ),
        (
            "            && !saved_tac_table_bottom_fits\n"
            "            && !st.current_items.is_empty())\n"
            "            || stored_vpos_rewind_break\n"
            f"            // {TAG} 앞에 쪽 번호 컨트롤이 있는 표는 첫 항목이 아니다. 자리가 모자라면 쪽 번호만 남기고 다음 쪽으로\n"
            "            || (st.profile.hwpx_container()\n"
            "                && st.current_height <= 0.5\n"
            "                && st.current_items.is_empty()\n"
            "                // 한/글이 저장한 줄이 표를 품고 있으면 그 쪽에 들어간 것이다(d100, d172). 더미나 합성 줄일 때만\n"
            "                && (para.line_segs.get(1).is_some_and(|s| s.vertical_pos == 0)\n"
            "                    || para.line_segs.first().is_some_and(|s| {\n"
            "                        s.tag & crate::model::paragraph::LineSeg::TAG_IMPLEMENTATION_PROPERTY == 0 && s.line_height * 2 < table.common.height as i32\n"
            "                    }))\n"
            "                && table_height.max(crate::renderer::hwpunit_to_px(table.common.height as i32, self.dpi)) + para.line_segs.first().map_or(0.0, |s| crate::renderer::hwpunit_to_px(s.line_height, self.dpi)) > available\n"
            "                && para.controls.iter().any(|c| matches!(c, Control::PageNumberPos(_))))\n"
            "        {\n"
            "            st.advance_column_or_new_page();\n"
            "        }\n"
        ),
    ),
]


def main():
    revert = "--revert" in sys.argv
    for rel, find, repl in EDITS:
        p = SRC / rel
        raw = p.read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in raw else "\n"
        s = raw.replace("\r\n", "\n")
        a, b = (repl, find) if revert else (find, repl)
        assert s.count(a) == 1, (rel, a[:70], s.count(a))
        p.write_bytes(s.replace(a, b).replace("\n", nl).encode("utf-8"))
    print("되돌림" if revert else "적용")


if __name__ == "__main__":
    main()
